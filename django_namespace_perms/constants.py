PERM_DENY = 0
PERM_READ = 0x01
PERM_WRITE = 0x02

PERM_CHOICES = [
  (PERM_READ, "read"),
  (PERM_WRITE, "write"),
  (PERM_READ|PERM_WRITE, "read & write"),
  (PERM_DENY, "deny"),
]
