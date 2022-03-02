# Patches

This folder contains patches on top of the hw-mgmt patch set that are required to maintain compatiblity with the upstream SONiC patches. 

### master

We have two patches in the master branch:

| Patch                                       | Notes                                                                                                                                                                                         |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Fix-linecard-regmap-access.patch            | Patch requested by Vadim Pasternack to disable some regmap calls for linecard devices that may cause issues.                                                                                  |
| Remove-pmbus-do-remove-dps460-dps1900.patch | We refactor the pmbus driver in hw-mgmt patches to remove the pmbus_do_remove statement. Upstream patches in SONiC add two new pmbus drivers which need to also be modified in this refactor. |
