# metal_ra
A Resident Advisor for Equinix Metal Organizational Accounting, AKA a rough cost calculator.

This tool, given an Equinix Metal [organization](https://deploy.equinix.com/developers/docs/metal/identity-access-management/organizations/) `id` and [User API token](https://deploy.equinix.com/developers/docs/metal/identity-access-management/api-keys/), will provide a report of:

1. On-demand: Return the email address of any user in the org that has instances that have been provisioned for more than 15 days, and calculate the MRC of those instances provisioned for that time. That 15 days is a magic number in the code.
2. Reserved: Return a list of projects where those projects have reservations older than 15 days, where the value of the project is determined by gathering the price of the reservation and adding 1 (many custom configurations return $0).

These reports come in the format of a `.json` file and `.csv` file for both on-demand and reserved.

* [Getting Started](docs/getting_started.md)

### Notes

This is not clean code and is not intended to represent good code by the author. It was a quick'n'dirty.
