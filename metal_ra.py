#!/usr/bin/env python3
"""
metal_ra.py
"""

__author__ = "dlotterman"
__version__ = "0.1.0"
__license__ = "Unlicense"

from logzero import logger
import equinix_metal
import os
import sys
import datetime
import time
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


# client = WebClient(token=slack_token)

AGE_LIMIT = 15

configuration = equinix_metal.Configuration(host="https://api.equinix.com/metal/v1")


def get_on_demand():
    instance_owners = {}
    page_count_total = 3
    page = 1
    reserved = False
    total_org_cost = 0
    monthly_org_cost = 0

    while page < page_count_total:
        with equinix_metal.ApiClient(configuration) as api_client:
            api_instance = equinix_metal.DevicesApi(api_client)
            id = ORG_ID

            max_retries = 3
            attempts = 0
            success = False
            while not success and attempts < max_retries:
                try:
                    per_page = 1
                    api_response = api_instance.find_organization_devices(
                        id, reserved=reserved, page=page, per_page=per_page
                    )
                    api_response_dict = api_response.to_dict()
                    page_count_total = api_response_dict["meta"].get("last_page")
                    logger.info(f"num pages in org devices list {page_count_total}")
                    logger.info(f"page num {page}")
                    page += 1
                    success = True
                    time.sleep(10)
                except equinix_metal.rest.ApiException as e:
                    logger.critical(f"Error{e}")
                except Exception as err:
                    logger.critical(f"{type(err).__name__} was raised: {err}")
                    time.sleep(10)
                    page += 1
                    attempts += 1

            for instance in api_response_dict.get("devices"):
                logger.info(instance.get("hostname"))
                instance_id = instance.get("id")
                instance_age = datetime.datetime.now(
                    datetime.timezone.utc
                ) - instance.get("created_at")

                instance_metro_id = instance["metro"].get("id")

                if instance_age.days < AGE_LIMIT:
                    logger.warning(f"instance to new {instance_id}")
                    break
                for available_metro in instance["plan"].get("available_in_metros"):
                    metro_href = available_metro.get("href")

                    if metro_href.endswith(instance_metro_id):
                        instance_price = available_metro.get("price")
                        if not instance_price:
                            instance_price_hour = 1
                        else:
                            instance_price_hour = instance_price.get("hour")
                instance_owner = instance["created_by"].get("email")
                instance_cost = round(instance_price_hour * 24 * instance_age.days)
                instance_cost_monthly = round(instance_price_hour * 730)

                if instance_owner not in instance_owners:
                    instance_owners[instance_owner] = {}
                    instance_owners[instance_owner]["total_owner_cost"] = instance_cost
                    instance_owners[instance_owner][
                        "monthly_owner_cost"
                    ] = instance_cost_monthly
                    instance_owners[instance_owner]["instances"] = []
                    instance_owners[instance_owner]["instances"].append(
                        instance.get("hostname")
                    )
                else:
                    new_cost = (
                        instance_owners[instance_owner].get("total_owner_cost")
                        + instance_cost
                    )
                    new_cost_monthly = (
                        instance_owners[instance_owner].get("monthly_owner_cost")
                        + instance_cost_monthly
                    )
                    instance_owners[instance_owner]["total_owner_cost"] = new_cost
                    instance_owners[instance_owner][
                        "monthly_owner_cost"
                    ] = instance_cost_monthly
                    instance_owners[instance_owner]["instances"].append(
                        instance.get("hostname")
                    )

    logger.info(instance_owners)
    return instance_owners


def get_reserved():
    page_count_total = 2
    page = 1

    org_projects = []
    reservations = []
    old_reservations = []
    reserve_cost_per_project = []

    while page < page_count_total:
        with equinix_metal.ApiClient(configuration) as api_client:
            api_instance = equinix_metal.OrganizationsApi(api_client)
            id = ORG_ID

            try:
                api_response = api_instance.find_organization_projects(id, page=page)
                api_response_dict = api_response.to_dict()
                page_count_total = api_response_dict["meta"].get("last_page")
                page += 1
            except Exception as err:
                logger.critical(f"{type(err).__name__} was raised: {err}")

            for project in api_response_dict.get("projects"):
                org_projects.append(project.get("id"))

    for project_id in org_projects:
        project_costs = 0

        with equinix_metal.ApiClient(configuration) as api_client:
            api_instance = equinix_metal.HardwareReservationsApi(api_client)

            try:
                api_response = api_instance.find_project_hardware_reservations(
                    project_id
                )
                api_response_dict = api_response.to_dict()
                for reservation in api_response_dict.get("hardware_reservations"):
                    if reservation.get("device") is not None:
                        reservation_age = datetime.datetime.now(
                            datetime.timezone.utc
                        ) - reservation.get("created_at")
                        if reservation_age.days > AGE_LIMIT:
                            new_cost = project_costs + round(
                                reservation["plan"]["pricing"].get("year") / 12
                            )
                            project_costs = new_cost
                if project_costs != 0:
                    reserve_cost_per_project.append({project_id: project_costs})
            except Exception as err:
                logger.critical(f"{type(err).__name__} was raised: {err}")

    logger.info(reserve_cost_per_project)

    return reserve_cost_per_project


def send_reserved_notification(reserved_audit):
    logger.info("starting notification")


def main():
    logger.info("starting metal_ra")
    on_demand_audit = get_on_demand()
    reserved_audit = get_reserved()

    send_reserved_notification(reserved_audit)


if __name__ == "__main__":
    if os.path.exists(os.path.expanduser("~") + "/.config/equinix/metal.yaml"):
        logger.info("metal-cli config found, using that for config")
        with open(
            os.path.expanduser("~") + "/.config/equinix/metal.yaml", "r"
        ) as f_metal_config:
            metal_config = f_metal_config.readlines()
            for line in metal_config:
                if ":" in line:
                    first, *middle, last = line.split()
                    if first == "organization-id:":
                        ORG_ID = last
                        logger.info(f"org-id: {ORG_ID}")
                    if first == "token:":
                        METAL_TOKEN = last
    elif os.environ["METAL_ORG_ID"] != "":
        ORG_ID = os.environ["METAL_ORG_ID"]
        METAL_TOKEN = os.environ["METAL_AUTH_TOKEN"]
    else:
        logger.critical(
            "must have metal-cli managed ~/.config/equinix/metal file or have environment variables set: METAL_ORG_ID, METAL_AUTH_TOKEN"
        )
        sys.exit(1)

    # slack_token = os.environ["SLACK_BOT_TOKEN"]
    configuration.api_key["x_auth_token"] = METAL_TOKEN

    main()
