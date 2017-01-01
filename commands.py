import subprocess

SYSTEMCTL = "/bin/systemctl"
WIFISWITCH = "/home/pi/bin/wifiswitch.sh"


def shutdown():
  print "Exec system shutdown now."
  print subprocess.check_output([SYSTEMCTL, "poweroff"])


def wifiswitch():
  print "Switching onto wifi network now."
  print subprocess.check_output([WIFISWITCH,])
