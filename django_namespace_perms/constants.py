
PERM_DENY = 0
PERM_READ = 0x01
PERM_WRITE = 0x02

#CRUD 
PERM_UPDATE = PERM_WRITE
PERM_CREATE = 0x04
PERM_DELETE = 0x08

PERM_CHOICES = [
  (PERM_READ, "read"),
  (PERM_WRITE, "write"),
  (PERM_READ|PERM_WRITE, "read & write"),
  (PERM_DENY, "deny"),
]
PERM_CHOICES_CRUD = [
  (PERM_READ, "read"),
  (PERM_UPDATE, "update"),
  (PERM_CREATE, "create"),
  (PERM_DELETE, "delete"),
  (PERM_DENY, "deny")
]

