###############################################################################
# Kickstart template used by create_provision_delete.py script.
###############################################################################

# Install Linux instead of upgrade
install

# Text mode install
text

# Network
network --bootproto=dhcp --device=eth0

# Use the following installation channels
url --url=http://oak.${zone}.guardis.be/public/centos/6.0/os/${vm_base_arch}/
repo --name=updates --baseurl=http://oak.${zone}.guardis.be/public/centos/6/updates/${vm_base_arch}/
repo --name=epel --baseurl=http://oak.${zone}.guardis.be/public/epel/6/${vm_base_arch}/

repo --name=comodit --baseurl=http://devel.bruxelles.guardis.be/public/comodit/centos/6/${vm_arch}/
<#if enable_trunk="true">
repo --name=comodit-dev --baseurl=http://devel.bruxelles.guardis.be/public/comodit-dev/centos/6/${vm_arch}/
</#if>

# Do not configure the X Window System
skipx

# System language
lang en_US

# System keyboard
keyboard be-latin1

# System timezone
timezone --utc Europe/Brussels

# Root password (here secret, should be changed ...)
rootpw ${ks_rootpw_one}

# Reboot after installation
reboot

# Run the Setup Agent on first boot
firstboot --disabled

# System authorization information
auth  --useshadow  --enablemd5

# Firewall configuration
firewall --enabled --ssh

# This is needed to create the VMs (has to be checked in the future releases)
selinux --permissive

# Installation logging level
logging --level=info

# Disable unnecessary services
services --disabled="MailScanner,anacron,apmd,atd,autofs,avahi-daemon,avahi-dnsconfd,barnyard,bluetooth,conman,cpuspeed,crond,cups,dansguardian,dhcdbd,dnsmasq,dund,firstboot,gpm,haldaemon,hidd,ibmasm,ip6tables,ipmi,iptables,ip6tables,irqbalance,kudzu,libvirtd,lm_sensors,lvm2-monitor,mcstrans,mdmonitor,mdmpd,messagebus,microcode_ctl,multipathd,netconsole,netfs,netplugd,nfs,nfslock,nrpe,nscd,ntpd,oddjobd,p3scan,pand,pcscd,pmacctd,portmap,psacct,qemu,rdisc,readahead_early,readahead_later,restorecond,rpcgssd,rpcidmapd,rpcsvcgssd,snortd,saslauthd,sendmail,setroubleshoot,smartd,sshd,syslog-ng,sysstat,xend,xendomains,xfs,ypbind,yum-updatesd"

# Enable necessary services
services --enabled="acpid,auditd,network,rsyslog,synapsed,sshd<#list _services as _service>,${_service}</#list>"

# Clear the Master Boot Record
zerombr

# System bootloader configuration
bootloader --location=mbr --append "text"

# Clear all partitions from the disk
clearpart --all

# Disk partitioning information
part /        --fstype ext4      --size=8 --grow
part swap  --fstype swap     --size=512

%packages --excludedocs --nobase
@Core

# usefull
acpid
vim-enhanced

# The additional distributions
epel-release

# Openssh
openssh
openssh-clients
openssh-server

# The yum system
yum

# For secure root execution
sudo

# For configuration management
synapse

# User specific packages
<#list _packages as _pack>
${_pack}
</#list>

%post

# Configure Synapse
cat << EOF > /etc/synapse/synapse.conf

[rabbitmq]
type = amqp
host = mahogany.angleur.guardis.be
queue = vm.${_hostid}
exchange = status
username = guest
password = guest

EOF

# Synapse for one time install
/usr/bin/synapse --uri ${_api}/organizations/${_orgName}/environments/${_envName}/hosts/${_hostName}/setup.json