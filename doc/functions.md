# Mapping between OpenVAS OMP and pyvas commands

Note that there are commands with missing equivalents in both 
directions. This can reflect that either the equivalent doesn't make 
sense, or that the functionality hasn't yet been implemented in pyvas.

| OpenVAS OMP 7.0 | pyvas            | Description |
| ----------------|------------------|------------------------------------------- |
|                 | _command  | Send, build and validate reponse |
|                 | _get      | Generic get function |
|                 | _map      | Generic function for mapping names to ids |
|                 | _list     | Generic list function |
|                 | _create   | Generic create function |
|                 | _modify   | Generic modify function |
|                 | _delete   | Generic delete function |
|                 | _send_request | Send XML data to OpenVAS manager and get results |
| authenticate    | authenticate     | Authenticate with the manager |
| commands        | | Run a list of commands |
| create_agent    | | Create an agent |
| create_alert    | | Create an alert |
| create_asset    | | Create an asset |
| create_config   | create_config | Copy a config |
|                 | copy_config_with_blacklist_by_name | Copies a config leaving out unwanted NVTs | 
|                 | copy_config_by_name | Copies a config by name |
| create_credential create_credential | Create a credential |
| create_filter   | | Create a filter |
| create_group    | | Create a group |
| create_note     | | Create a note |
| create_override | | Create an override |
| create_permission | | Create a permission |
| create_port_list | create_port_list | Create a port list |
| create_port_range | | Create a port range |
| create_report   | | Create a report |
| create_report_format | | Create a report format |
| create_role     | | Create a role |
| create_scanner  | | Create a scanner |
| create_schedule | create_schedule | Create a schedule |
| create_tag      | | Create a tag |
| create_target   | create_target | Create a target |
| create_task     | create_task | Create a task |
| create_user     | | Create a user |
| delete_alert    | | Delete an alert |
| delete_asset    | | Delete an asset |
| delete_config   | delete_config, delete_config_by_name | Delete a config |
| delete_credential | Delete a credential |
| delete_filter   | | Delete a filter |
| delete_group    | | Delete a group |
| delete_note     | | Delete a note |
| delete_override | | Delete an override |
| delete_permission | | Delete a permission |
| delete_port_list | delete_port_list | Delete a port list |
| delete_port_range | | Delete a port range |
| delete_report   | delete_report | Delete a report |
| delete_report_format | | Delete a report format |
| delete_role     | | Delete a role |
| delete_scanner  | | Delete a scanner |
| delete_schedule | delete_schedule | Delete a schedule |
| delete_tag      | | Delete a tag |
| delete_target   | delete_target | Delete a target |
| delete_task     | delete_task | Delete a task |
| delete_user     | | Delete a user |
| describe_auth   | | Describe authentication methods |
| empty_trashcan  | | Empty the trashcan |
| get_agents      | | Get one or many agents |
| get_configs     | list_configs, get_config, get_config_by_name | Get one or many configs |
|                 | map_config_names | Create a dictionary of config names mapped to config ids |
|                 | list_config_nvts | Lists all of the NVTs used by the given config |
|                 | list_config_families | Lists all of the NVT families used by the given config |
|                 | config_remove_nvt | Modifies a config by removing one nvt that it uses |
| get_aggregates  | | Get aggregates of various resources |
| get_alerts      | | Get one or many alerts |
| get_assets      | | Get one or many assets |
| get_credentials | | Get one or many credentials |
| get_feeds       | | Get one or many feeds |
| get_filters     | | Get one or many filters |
| get_groups      | | Get one or many groups |
| get_info        | | Get information for items of a given type |
| get_notes       | | Get one or many notes |
| get_nvts        |list_nvts, get_nvt | Get one or many NVTs |
|      | map_nvts | Return a dictionary mapping NVT families to lists of the NVTs that they contain |
| get_nvt_families | list_nvt_families, get_nvt_family | Get one or many NVT families |
|      | get_nvt_family | Return the id of the family that the NVT is a member of |
| get_overrides   | | Get one or many overrides |
| get_permissions | | Get one or many permissions |
| get_port_lists  | list_port_lists, get_port_list | Get one or many port lists |
| get_preferences | | Get one or many preferences |
| get_reports     | list_report, get_report, download_report | Get one or many reports |
| get_report_formats | list_report_formats, get_report_format | Get one or many report formats |
| get_results     | list_results, get_result | Get one or many results |
| get_roles       | | Get one or many roles |
| get_scanners    | list_scanners, get_scanner | Get one or many scanners |
| get_schedules   | list_schedules, get_schedule | Get one or many schedules |
| get_settings    | | Get one or many settings |
| get_system_reports | | Get one or many system reports |
| get_tags        | | Get one or many tags |
| get_targets     | list_targets, get_target | Get one or many targets |
| get_tasks       | list_tasks, get_task | Get one or many tasks |
|                 | map_task_names | Create a dictionary of task names mapped to task ids |
| get_users       | | Get one or many users |
| get_version     | | Get the OpenVAS Manager Protocol version |
| help            | | Get the help text |
| modify_agent    | | Modify an existing agent |
| modify_alert    | | Modify an existing alert |
| modify_asset    | | Modify an existing asset |
| modify_auth     | | Modify an existing auth |
| modify_config   | | Modify an existing config |
| modify_credential | | Modify an existing credential |
| modify_filter   | | Modify an existing filter |
| modify_group    | | Modify an existing group |
| modify_note     | | Modify an existing note |
| modify_override | | Modify an existing override |
| modify_permission | | Modify an existing permission |
| modify_port_list | | Modify an existing port list |
| modify_port_range | | Modify an existing port range |
| modify_report   | | Modify an existing report |
| modify_report_format | | Modify an existing report format |
| modify_role     | | Modify an existing role |
| modify_scanner  | | Modify an existing scanner |
| modify_schedule | modify_schedule | Modify an existing schedule |
| modify_setting  | | Modify an existing setting |
| modify_tag      | | Modify an existing tag |
| modify_target   | modify_target | Modify an existing target |
| modify_task     | | Modify an existing task |
| modify_user     | | Modify an existing user |
| move_task       | | Move an existing task to another OMP slave scanner or the master |
| restore         | | Restore a resource |
| resume_task     | resume_task | Resume a task |
|                 | resume_task_by_name | Resume a task by name instead of by id |
| run_wizard      | | Run the wizard |
| start_task      | start_task | Manually start an existing task |
|                 | start_task_by_name | Start a task by name instead of by id |
| stop_task       | stop_task | Stop a running task |
|                 | stop_task_by_name | Stop a task by name instead of by id |
| sync_cert       | | Synchronise with a CERT feed |
| sync_feed       | | Synchronise with an NVT feed |
| sync_config     | | Synchronise config with a scanner |
| sync_scap       | | Synchronise with a SCAP feed |
| test_alert      | | Run an alert |
| verify_agent    | | Verify an agent |
| verify_report_format | | Verify a report format |
| verify_scanner  | | Verify a scanner |

## Further information

* OpenVAS Project OMP Documentation - (http://docs.greenbone.net/API/OMP/omp-7.0.html)

## Authors

* **Anna Langley** - *Initial work on this document* - (https://github.com/jal58)

## Acknowledgments

* Martin Picard (original developer of pyvas) - (https://github.com/mpicard)
