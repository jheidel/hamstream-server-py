import subprocess

SYSTEMCTL = "/bin/systemctl"


def shutdown():
  print "Exec system shutdown now."
  print subprocess.check_output([SYSTEMCTL, "poweroff"])
