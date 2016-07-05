
PERM_DENY = 0

# if NSP_MODE is unset or set to "rw", PERM_WRITE will give
# access to all writes
PERM_READ = 0x01
PERM_WRITE = 0x02

# if NSP_MODE is set to "crud", permission flags for write operations
# will be more granular
PERM_UPDATE = PERM_WRITE
PERM_CREATE = 0x04
PERM_DELETE = 0x08

PERM_CRUD = PERM_CREATE | PERM_READ | PERM_UPDATE | PERM_DELETE

PERM_CHOICES = [
  (PERM_READ, "read"),
  (PERM_WRITE, "write"),
  (PERM_DENY, "deny"),
]
PERM_CHOICES_CRUD = [
  (PERM_READ, "read"),
  (PERM_UPDATE, "update"),
  (PERM_CREATE, "create"),
  (PERM_DELETE, "delete"),
  (PERM_DENY, "deny")
]

