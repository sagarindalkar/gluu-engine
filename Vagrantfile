# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure(2) do |config|
  config.vm.box = "phusion/ubuntu-14.04-amd64"

  # master
  config.vm.define "master", primary: true do |master|
    master.vm.hostname = "gluu-master"
    master.vm.synced_folder ".", "/gluu-flask"
    master.vm.network "private_network", ip: "172.20.20.10"

    master.vm.provision "shell", inline: <<-SHELL
      wget -q http://repo.gluu.org/ubuntu/gluu-release-devel_1.0-1_all.deb -O /tmp/gluu-release-devel_1.0-1_all.deb
      dpkg -i /tmp/gluu-release-devel_1.0-1_all.deb
      apt-get update -q
      apt-get install -y gluu-master python-pip python-dev swig libsasl2-dev libldap2-dev libssl-dev
      pip install tox
    SHELL
  end

  # consumer
  config.vm.define "consumer", autostart: false do |consumer|
    consumer.vm.hostname = "gluu-consumer"
    consumer.vm.network "private_network", ip: "172.20.20.11"

    consumer.vm.provision "shell", inline: <<-SHELL
      wget -q http://repo.gluu.org/ubuntu/gluu-release-devel_1.0-1_all.deb -O /tmp/gluu-release-devel_1.0-1_all.deb
      dpkg -i /tmp/gluu-release-devel_1.0-1_all.deb
      apt-get update -q
    SHELL
  end
end
