# Vagrantfile: describe la maquina virtual (VM) que hace de servidor.
Vagrant.configure("2") do |config|

  # Sistema operativo de la VM: Ubuntu 24.04
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.hostname = "bodega-server"

  # NUEVO: le da mas tiempo a la VM para arrancar (10 min)
  config.vm.boot_timeout = 600

  # REENVIO DE PUERTO: lo que llegue al puerto 5000 de Windows pasa a la VM.
  # host_ip 0.0.0.0 = acepta conexiones de cualquier equipo de la red (ESP32, celular)
  config.vm.network "forwarded_port", guest: 5000, host: 5000, host_ip: "0.0.0.0"

  # Recursos de la VM
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
    # NUEVO: asegura que el "cable" de red virtual este conectado
    vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
  end

  # APROVISIONAMIENTO: instala Docker automaticamente al crear la VM
  config.vm.provision "shell", inline: <<-SHELL
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker vagrant
  SHELL
end
