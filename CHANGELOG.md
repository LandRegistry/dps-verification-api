# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and as of version 3.0.0 this project adheres to [Semantic Versioning](http://semver.org/).

## [2.12.0]

### Updated

- Python 3.6 upgrade

## [2.11.0]

### Added

- Ability to add 'next steps' when declining an application

## [2.10.0]

### Amended

- DST action event sent to akuma when group updated

## [2.9.0]

### Added

- Backend functionality for new contact preferences page
- trace_id included in audit point

## [2.8.0]

### Updated

- Updated CKAN dependency to now use ulapd-api

## [2.7.0]

### Added

- Audit events for:
    - Approve success/error
    - Decline success/error
    - Close success/error
    - Contact prefs update success/error
    - Dataset access (groups) update success/error

## [2.6.0]

### Added

- New route for account api to automatically close accounts
    - Mark account as closed in DB
    - Add note for warning/close email sent to user

## [2.5.0]

### Added

- New Route to get a user's dataset activity, including licences agreed and download history

## [2.4.0]

### Added

- Route to retrieve list of datasets in service with more details than just the name of the dataset
- Route to retrieve list of datasets that the user has access by retrieving case details from verification table
- Route to update ldap with any changes to a users data access on ldap via account_api

## [2.3.0]

### Added

- Record the change in a users contact preference and add a notepad entry to reflect the change.  Also calls ckan to amend the contact preference

## [2.2.0]

### Added

- Call to dps_metric_api to record metric information for applications received and dst actions(approve, decline, close)

## [2.1.0]

### Added

- Close account endpoint now sends akuma event.

## [2.0.1]

### Added

- Close account endpoint now sends 'requester' in the account-api call to allow sending user email.

## Changed

- Close account endpoint now calls the service to add a note.

## [2.0.0]

## Changed

- All endpoints acting upon cases now require the case_id in the URL instead of request body.

## Fixed

- 200 "OK" responses are no longer returned with HTTP status 201

## [1.5.0]

### Added

- /search endpoint

## [1.4.0]

### Added

- `/lock` and `/unlock` endpoints

### Changed

- Case locking is now taken into consideration by approval, decline and note-adding functions
- `/details` now returns 404 for case not found instead of 200 with empty JSON object
- All endpoints now return JSON under all circumstances, including errors

### Fixed

- Integration tests no longer wipe the entire DST database during teardown
- Teardown is now more comprehensive, preventing bleeding of LDAP test data and failure of subsequent test runs

## [1.3.0]

### Added

- `/close` endpoint to allow DST users to close service user accounts

## [1.2.1]

### Fixed

- Removed tests for `_create_dict` method which was removed from codebase

## [1.2.0]

### Added

- In progress status to worklist items

## [1.1.0]

### Added

- Call to Akuma added to dependencies
- Function added to set up the data for the call to Akuma
- Retry count added as an environment variable for the call to Akuma

### Changed

- Routes for approve, decline and insert case amended to call the new Akuma function

## [1.0.1]

### Changed

- Amended the sort order of notes to display in the notepad in descending date order (newest note at the top)

## [1.0.0]

### Added

- The very first release for private beta
