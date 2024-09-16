# __main__.py
# Main entry point for the Kargo Pulumi IaC program.
# This script is responsible for deploying the Kargo platform components.

# Import Pulumi Libraries
import pulumi
import pulumi_kubernetes as k8s

# Import Python Standard Libraries
from typing import Any, Dict, List, Optional, Tuple

# Local imports
from src.lib.init import initialize_pulumi
from src.lib.config import get_module_config, export_results

# Pulumi Initialization
init = initialize_pulumi()

# Retrieve initialized resources
config = init["config"]
k8s_provider = init["k8s_provider"]
versions = init["versions"]
configurations = init["configurations"]
default_versions = init["default_versions"]
global_depends_on = init["global_depends_on"]
compliance_config = init["compliance_config"]

##########################################
# Deploy Moudles from ./src/<module_name>

def deploy_module(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, Any],
    global_depends_on: List[pulumi.Resource],
    k8s_provider: Any,
    deploy_function: Any,
    export_name: str
) -> None:
    """
    Helper function to deploy a module based on configuration.

    Args:
        module_name (str): Name of the module.
        config (pulumi.Config): Pulumi configuration object.
        default_versions (Dict[str, Any]): Default versions for modules.
        global_depends_on (List[pulumi.Resource]): Global dependencies.
        k8s_provider (Any): Kubernetes provider.
        deploy_function (Callable): Function to deploy the module.
        export_name (str): Name of the export variable.
    """
    module_config_dict, module_enabled = get_module_config(module_name, config, default_versions)

    if module_enabled:
        # Dynamically import the module's types and deploy function
        module_types = __import__(f"src.{module_name}.types", fromlist=[''])
        ModuleConfigClass = getattr(module_types, f"{module_name.capitalize()}Config")
        config_obj = ModuleConfigClass.merge(module_config_dict)

        module_deploy = __import__(f"src.{module_name}.deploy", fromlist=[''])
        deploy_func = getattr(module_deploy, f"deploy_{module_name}_module")

        version, release, exported_value = deploy_func(
            config_obj=config_obj,
            global_depends_on=global_depends_on,
            k8s_provider=k8s_provider,
        )

        versions[module_name] = version
        configurations[module_name] = {
            "enabled": module_enabled,
        }

        pulumi.export(export_name, exported_value)

##########################################
# Deploy Cert Manager Module

# Retrieve configuration and enable flag for the cert_manager module
config_cert_manager_dict, cert_manager_enabled = get_module_config(
    'cert_manager',
    config,
    default_versions,
)

# Check if the cert_manager module is enabled & execute deployment logic if true
if cert_manager_enabled:
    from src.cert_manager.types import CertManagerConfig
    from src.cert_manager.deploy import deploy_cert_manager_module
    config_cert_manager = CertManagerConfig.merge(config_cert_manager_dict)

    cert_manager_version, cert_manager_release, cert_manager_selfsigned_cert = deploy_cert_manager_module(
        config_cert_manager=config_cert_manager,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Record the deployed version and configuration
    versions["cert_manager"] = cert_manager_version
    configurations["cert_manager"] = {
        "enabled": cert_manager_enabled,
    }

    # append cert_manager_release to global_depends_on
    global_depends_on.append(cert_manager_release)

    pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)
else:
    cert_manager_selfsigned_cert = None

##########################################
# Deploy KubeVirt Module

# Retrieve configuration and enable flag for the kubevirt module
config_kubevirt_dict, kubevirt_enabled = get_module_config(
    'kubevirt',
    config,
    default_versions,
)

# Check if the kubevirt module is enabled & execute deployment logic if true
if kubevirt_enabled:
    from src.kubevirt.types import KubeVirtConfig
    from src.kubevirt.deploy import deploy_kubevirt_module
    config_kubevirt = KubeVirtConfig.merge(config_kubevirt_dict)

    # Pass cert_manager_release as a dependency if cert_manager is enabled
    kubevirt_version, kubevirt_operator = deploy_kubevirt_module(
        config_kubevirt=config_kubevirt,
        global_depends_on=global_depends_on,
        k8s_provider=k8s_provider,
    )

    # Record the deployed version and configuration
    versions["kubevirt"] = kubevirt_version
    configurations["kubevirt"] = {
        "enabled": kubevirt_enabled,
    }

    pulumi.export("kubevirt_version", kubevirt_version)
else:
    kubevirt_version = None

##########################################
# Export Component Metadata Outputs:
# - Versions
# - Configurations
export_results(versions, configurations, compliance_config)



############################################
## Deploy Kubevirt Module
#
## KubeVirt Module Configuration and Deployment
#config_kubevirt_dict, kubevirt_enabled = get_module_config('kubevirt', config, default_versions)
#
#if kubevirt_enabled:
#    # Import the KubeVirtConfig data class and merge the user config with defaults
#    from src.kubevirt.types import KubeVirtConfig
#    config_kubevirt = KubeVirtConfig.merge(config_kubevirt_dict)
#
#    # Import the deployment function for the KubeVirt module
#    from src.kubevirt.deploy import deploy_kubevirt_module
#
#    # Deploy the KubeVirt module
#    kubevirt_version, kubevirt_operator = deploy_kubevirt_module(
#        config_kubevirt=config_kubevirt,
#        global_depends_on=global_depends_on,
#        k8s_provider=k8s_provider,
#    )
#
#    # Apply Git and compliance metadata to KubeVirt
#    apply_git_metadata(kubevirt_operator, git_info)
#    apply_compliance_metadata(kubevirt_operator, compliance_config.__dict__)
#
#    # Record the deployed version & configuration
#    versions["kubevirt"] = kubevirt_version
#    configurations["kubevirt"] = {
#        "enabled": kubevirt_enabled
#    }
#else:
#    kubevirt_operator = None


#from src.kubevirt.deploy import deploy_kubevirt
#from src.containerized_data_importer.deploy import deploy_cdi
#from src.cluster_network_addons.deploy import deploy_cnao
#from src.multus.deploy import deploy_multus
#from src.hostpath_provisioner.deploy import deploy as deploy_hostpath_provisioner
#from src.openunison.deploy import deploy_openunison
#from src.prometheus.deploy import deploy_prometheus
#from src.kubernetes_dashboard.deploy import deploy_kubernetes_dashboard
#from src.kv_manager.deploy import deploy_ui_for_kubevirt
#from src.ceph.deploy import deploy_rook_operator
#from src.vm.ubuntu import deploy_ubuntu_vm
#from src.vm.talos import deploy_talos_cluster
#from src.cilium.deploy import deploy_cilium
#
###########################################
## Kubernetes Configuration
#kubernetes_config = config.get_object("kubernetes") or {}
#kubeconfig = kubernetes_config.get("kubeconfig")
#kubernetes_context = kubernetes_config.get("context")
#
## Create a Kubernetes provider instance
#k8s_provider = Provider(
#    "k8sProvider",
#    kubeconfig=kubeconfig,
#    context=kubernetes_context,
#)
#
## Initialize versions dictionary to track deployed component versions
#versions: Dict[str, Dict[str, Any]] = {}
#
###########################################
## Module Configuration and Enable Flags
#
## Retrieve configurations and enable flags for all modules
#config_cilium, cilium_enabled = get_module_config('cilium')
#config_cert_manager, cert_manager_enabled = get_module_config('cert_manager')
#config_kubevirt, kubevirt_enabled = get_module_config('kubevirt')
#config_cdi, cdi_enabled = get_module_config('cdi')
#config_multus, multus_enabled = get_module_config('multus')
#config_prometheus, prometheus_enabled = get_module_config('prometheus')
#config_openunison, openunison_enabled = get_module_config('openunison')
#config_hostpath_provisioner, hostpath_provisioner_enabled = get_module_config('hostpath_provisioner')
#config_cnao, cnao_enabled = get_module_config('cnao')
#config_kubernetes_dashboard, kubernetes_dashboard_enabled = get_module_config('kubernetes_dashboard')
#config_kubevirt_manager, kubevirt_manager_enabled = get_module_config('kubevirt_manager')
#config_vm, vm_enabled = get_module_config('vm')
#config_talos, talos_cluster_enabled = get_module_config('talos')
#
###########################################
## Dependency Management
#
## Initialize a list to keep track of dependencies between resources
#global_depends_on: List[pulumi.Resource] = []
#
###########################################
## Export Component Versions
#
#pulumi.export("versions", versions)

#def deploy_kubevirt_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the KubeVirt module if enabled.
#
#    Returns:
#        A tuple containing the version and the KubeVirt operator resource.
#    """
#    if not kubevirt_enabled:
#        pulumi.log.info("KubeVirt module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kubevirt"
#    kubevirt_version = config_kubevirt.get('version')
#    kubevirt_emulation = config_kubevirt.get('emulation', False)
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#
#    kubevirt_version, kubevirt_operator = deploy_kubevirt(
#        depends_on=depends_on,
#        namespace=namespace,
#        version=kubevirt_version,
#        emulation=kubevirt_emulation,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["kubevirt"] = {"enabled": kubevirt_enabled, "version": kubevirt_version}
#
#    if kubevirt_operator:
#        global_depends_on.append(kubevirt_operator)
#
#    return kubevirt_version, kubevirt_operator
#
#def deploy_multus_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Multus module if enabled.
#
#    Returns:
#        A tuple containing the version and the Multus Helm release resource.
#    """
#    if not multus_enabled:
#        pulumi.log.info("Multus module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "multus"
#    multus_version = config_multus.get('version', "master")
#    bridge_name = config_multus.get('bridge_name', "br0")
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#
#    multus_version, multus_release = deploy_multus(
#        depends_on=depends_on,
#        version=multus_version,
#        bridge_name=bridge_name,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["multus"] = {"enabled": multus_enabled, "version": multus_version}
#
#    if multus_release:
#        global_depends_on.append(multus_release)
#
#    return multus_version, multus_release
#
#def deploy_hostpath_provisioner_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the HostPath Provisioner module if enabled.
#
#    Returns:
#        A tuple containing the version and the Helm release resource.
#    """
#    if not hostpath_provisioner_enabled:
#        pulumi.log.info("HostPath Provisioner module is disabled. Skipping deployment.")
#        return None, None
#
#    if not cert_manager_enabled:
#        error_msg = "HostPath Provisioner requires Cert Manager. Please enable Cert Manager and try again."
#        pulumi.log.error(error_msg)
#        raise Exception(error_msg)
#
#    namespace = "hostpath-provisioner"
#    hostpath_version = config_hostpath_provisioner.get('version')
#    default_path = config_hostpath_provisioner.get('default_path', "/var/mnt/hostpath-provisioner")
#    default_storage_class = config_hostpath_provisioner.get('default_storage_class', False)
#
#    depends_on = []
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#    if kubevirt_enabled:
#        depends_on.append(kubevirt_operator)
#
#    hostpath_version, hostpath_release = deploy_hostpath_provisioner(
#        depends_on=depends_on,
#        version=hostpath_version,
#        namespace=namespace,
#        default_path=default_path,
#        default_storage_class=default_storage_class,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["hostpath_provisioner"] = {"enabled": hostpath_provisioner_enabled, "version": hostpath_version}
#
#    if hostpath_release:
#        global_depends_on.append(hostpath_release)
#
#    return hostpath_version, hostpath_release
#
#def deploy_cdi_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Containerized Data Importer (CDI) module if enabled.
#
#    Returns:
#        A tuple containing the version and the CDI Helm release resource.
#    """
#    if not cdi_enabled:
#        pulumi.log.info("CDI module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "cdi"
#    cdi_version = config_cdi.get('version')
#
#    cdi_version, cdi_release = deploy_cdi(
#        depends_on=global_depends_on,
#        version=cdi_version,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["cdi"] = {"enabled": cdi_enabled, "version": cdi_version}
#
#    if cdi_release:
#        global_depends_on.append(cdi_release)
#
#    return cdi_version, cdi_release
#
#def deploy_prometheus_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Prometheus module if enabled.
#
#    Returns:
#        A tuple containing the version and the Prometheus Helm release resource.
#    """
#    if not prometheus_enabled:
#        pulumi.log.info("Prometheus module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "monitoring"
#    prometheus_version = config_prometheus.get('version')
#
#    prometheus_version, prometheus_release = deploy_prometheus(
#        depends_on=global_depends_on,
#        namespace=namespace,
#        version=prometheus_version,
#        k8s_provider=k8s_provider,
#        openunison_enabled=openunison_enabled,
#    )
#
#    versions["prometheus"] = {"enabled": prometheus_enabled, "version": prometheus_version}
#
#    if prometheus_release:
#        global_depends_on.append(prometheus_release)
#
#    return prometheus_version, prometheus_release
#
#def deploy_kubernetes_dashboard_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Kubernetes Dashboard module if enabled.
#
#    Returns:
#        A tuple containing the version and the Dashboard Helm release resource.
#    """
#    if not kubernetes_dashboard_enabled:
#        pulumi.log.info("Kubernetes Dashboard module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kubernetes-dashboard"
#    dashboard_version = config_kubernetes_dashboard.get('version')
#
#    depends_on = global_depends_on.copy()
#    if cilium_enabled:
#        depends_on.append(cilium_release)
#
#    dashboard_version, dashboard_release = deploy_kubernetes_dashboard(
#        depends_on=depends_on,
#        namespace=namespace,
#        version=dashboard_version,
#        k8s_provider=k8s_provider,
#    )
#
#    versions["kubernetes_dashboard"] = {"enabled": kubernetes_dashboard_enabled, "version": dashboard_version}
#
#    if dashboard_release:
#        global_depends_on.append(dashboard_release)
#
#    return dashboard_version, dashboard_release
#
#def deploy_openunison_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the OpenUnison module if enabled.
#
#    Returns:
#        A tuple containing the version and the OpenUnison Helm release resource.
#    """
#    if not openunison_enabled:
#        pulumi.log.info("OpenUnison module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "openunison"
#    openunison_version = config_openunison.get('version')
#    domain_suffix = config_openunison.get('dns_suffix', "kargo.arpa")
#    cluster_issuer = config_openunison.get('cluster_issuer', "cluster-selfsigned-issuer-ca")
#
#    github_config = config_openunison.get('github', {})
#    github_client_id = github_config.get('client_id')
#    github_client_secret = github_config.get('client_secret')
#    github_teams = github_config.get('teams')
#
#    if not github_client_id or not github_client_secret:
#        error_msg = "OpenUnison requires GitHub OAuth credentials. Please provide 'client_id' and 'client_secret' in the configuration."
#        pulumi.log.error(error_msg)
#        raise Exception(error_msg)
#
#    enabled_components = {
#        "kubevirt": {"enabled": kubevirt_enabled},
#        "prometheus": {"enabled": prometheus_enabled},
#    }
#
#    pulumi.export("enabled_components", enabled_components)
#
#    openunison_version, openunison_release = deploy_openunison(
#        depends_on=global_depends_on,
#        namespace=namespace,
#        version=openunison_version,
#        k8s_provider=k8s_provider,
#        domain_suffix=domain_suffix,
#        cluster_issuer=cluster_issuer,
#        ca_cert_b64=cert_manager_selfsigned_cert,
#        kubernetes_dashboard_release=kubernetes_dashboard_release,
#        github_client_id=github_client_id,
#        github_client_secret=github_client_secret,
#        github_teams=github_teams,
#        enabled_components=enabled_components,
#    )
#
#    versions["openunison"] = {"enabled": openunison_enabled, "version": openunison_version}
#
#    if openunison_release:
#        global_depends_on.append(openunison_release)
#
#    return openunison_version, openunison_release
#
#def deploy_ubuntu_vm_module() -> Tuple[Optional[Any], Optional[Any]]:
#    """
#    Deploys an Ubuntu VM using KubeVirt if enabled.
#
#    Returns:
#        A tuple containing the VM resource and the SSH service resource.
#    """
#    if not vm_enabled:
#        pulumi.log.info("Ubuntu VM module is disabled. Skipping deployment.")
#        return None, None
#
#    # Get the SSH public key from Pulumi Config or local filesystem
#    ssh_pub_key = config.get("ssh_pub_key")
#    if not ssh_pub_key:
#        ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
#        try:
#            with open(ssh_key_path, "r") as f:
#                ssh_pub_key = f.read().strip()
#        except FileNotFoundError:
#            error_msg = f"SSH public key not found at {ssh_key_path}. Please provide 'ssh_pub_key' in the configuration."
#            pulumi.log.error(error_msg)
#            raise Exception(error_msg)
#
#    # Merge default VM configuration with user-provided configuration
#    default_vm_config = {
#        "namespace": "default",
#        "instance_name": "ubuntu",
#        "image_name": "docker.io/containercraft/ubuntu:22.04",
#        "node_port": 30590,
#        "ssh_user": "kc2",
#        "ssh_password": "kc2",
#        "ssh_pub_key": ssh_pub_key,
#    }
#
#    vm_config = {**default_vm_config, **config_vm}
#
#    # Deploy the Ubuntu VM
#    ubuntu_vm, ssh_service = deploy_ubuntu_vm(
#        vm_config=vm_config,
#        k8s_provider=k8s_provider,
#        depends_on=global_depends_on,
#    )
#
#    versions["ubuntu_vm"] = {"enabled": vm_enabled, "name": ubuntu_vm.metadata["name"]}
#
#    if ssh_service:
#        global_depends_on.append(ssh_service)
#
#    return ubuntu_vm, ssh_service
#
#def deploy_talos_cluster_module() -> Tuple[Optional[Any], Optional[Any]]:
#    """
#    Deploys a Talos cluster using KubeVirt if enabled.
#
#    Returns:
#        A tuple containing the control plane VM pool and the worker VM pool resources.
#    """
#    if not talos_cluster_enabled:
#        pulumi.log.info("Talos cluster module is disabled. Skipping deployment.")
#        return None, None
#
#    depends_on = []
#    if cert_manager_enabled:
#        depends_on.append(cert_manager_release)
#    if multus_enabled:
#        depends_on.append(multus_release)
#    if cdi_enabled:
#        depends_on.append(cdi_release)
#
#    controlplane_vm_pool, worker_vm_pool = deploy_talos_cluster(
#        config_talos=config_talos,
#        k8s_provider=k8s_provider,
#        parent=kubevirt_operator,
#        depends_on=depends_on,
#    )
#
#    versions["talos_cluster"] = {
#        "enabled": talos_cluster_enabled,
#        "running": config_talos.get("running", True),
#        "controlplane": config_talos.get("controlplane", {}),
#        "workers": config_talos.get("workers", {}),
#    }
#
#    return controlplane_vm_pool, worker_vm_pool

# Deactivating Cilium module deployment until Talos 1.8 releases with cni optimizations
#def deploy_cilium_module() -> Tuple[Optional[str], Optional[pulumi.Resource]]:
#    """
#    Deploys the Cilium CNI module if enabled.
#
#    Returns:
#        A tuple containing the Cilium version and the Helm release resource.
#    """
#    if not cilium_enabled:
#        pulumi.log.info("Cilium module is disabled. Skipping deployment.")
#        return None, None
#
#    namespace = "kube-system"
#    l2_announcements = config_cilium.get('l2announcements', "192.168.1.70/28")
#    l2_bridge_name = config_cilium.get('l2_bridge_name', "br0")
#    cilium_version = config_cilium.get('version')
#
#    # Deploy Cilium using the provided parameters
#    cilium_version, cilium_release = deploy_cilium(
#        name="cilium-cni",
#        provider=k8s_provider,
#        project_name=project_name,
#        kubernetes_endpoint_service_address=None,  # Replace with actual endpoint if needed
#        namespace=namespace,
#        version=cilium_version,
#        l2_bridge_name=l2_bridge_name,
#        l2announcements=l2_announcements,
#    )
#
#    versions["cilium"] = {"enabled": cilium_enabled, "version": cilium_version}
#
#    # Add the release to the global dependencies
#    if cilium_release:
#        global_depends_on.append(cilium_release)
#
#    return cilium_version, cilium_release

#kubevirt_version, kubevirt_operator = deploy_kubevirt_module()
#multus_version, multus_release = deploy_multus_module()
#hostpath_version, hostpath_release = deploy_hostpath_provisioner_module()
#cdi_version, cdi_release = deploy_cdi_module()
#prometheus_version, prometheus_release = deploy_prometheus_module()
#dashboard_version, kubernetes_dashboard_release = deploy_kubernetes_dashboard_module()
#openunison_version, openunison_release = deploy_openunison_module()
#ubuntu_vm, ubuntu_ssh_service = deploy_ubuntu_vm_module()
#talos_controlplane_vm_pool, talos_worker_vm_pool = deploy_talos_cluster_module()
#cilium_version, cilium_release = deploy_cilium_module()
