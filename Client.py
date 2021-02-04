import os
import time
from os import path
import yaml
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import NewConnectionError, MaxRetryError, ConnectTimeoutError
from kubernetes.stream import stream

from Logger import Logger


class Client:
    # A class for instantiate Kubernetes Client and its resources
    PODS_HEADER = "<Available Pods>"
    DEPLOYMENT_HEADER = "<Available Deployments>"
    PODS_LIST_DISPLAY_FORMAT = "  {:<21}{:<45}{:<10}{:<10}{:<16}{:<20}{:<20}{}"
    PODS_LIST_HEADER_DISPLAY_FORMAT = PODS_LIST_DISPLAY_FORMAT.format("NAMESPACE", "NAME", "STATUS", "RESTARTS", "IP",
                                                                      "NODE", "NOMINATED NODE", "READINESS GATES")
    DEPLOYMENT_LIST_DISPLAY_FORMAT = "  {:<35}{:<12}{:<12}{}"
    DEPLOYMENT_LIST_HEADER_DISPLAY_FORMAT = DEPLOYMENT_LIST_DISPLAY_FORMAT.format("NAME", "READY", "UP-TO-DATE",
                                                                                  "AVAILABLE")
    MSG_WARN_NO_PODS = "There is no {}Pods at this moment.."
    MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER = "Unable to connect to k8 cluster"
    MSG_INFO_POD_CREATED = "Pod[type=Deployment] created. status={}"
    MSG_WARN_NO_DEPLOYMENT = "There is no {}deployment at this moment.."
    MSG_INFO_POD_DEPLOYED = "Pod[type=DaemonSet] deployed. status={}"

    def __init__(self):
        # client instance
        kube_config_filepath = os.getenv("KUBECONFIG") or "~/.kube/config"
        try:
            config_file = os.path.expanduser(kube_config_filepath)
            config.load_kube_config(config_file=config_file)
        except:
            Logger.warn("unable to load kube-config")
        self.api_instance = client.CoreV1Api()
        self.apps_api_instance = client.AppsV1Api()
        self.apps_api_beta1_instance = client.AppsV1beta1Api()

    def list_all_pods(self, all_flag):
        # get all pods
        try:
            result_pods_list = []
            if all_flag:
                pods_list = self.api_instance.list_pod_for_all_namespaces(watch=False)
            else:
                pods_list = self.api_instance.list_namespaced_pod("default")
            pods = pods_list.items
            if pods is None or len(pods_list.items) == 0:
                Logger.warn(self.MSG_WARN_NO_PODS.format("Available "))
                return result_pods_list
            else:
                Logger.header(self.PODS_HEADER)
                Logger.sub_info(self.PODS_LIST_HEADER_DISPLAY_FORMAT.format("Available"))
                trunk_len_mid = 20
                trunk_len_big = 41
                for pod in pods:
                    pod.metadata.name = "NA" if pod.metadata.name is None else pod.metadata.name
                    result_pods_list.append(pod.metadata.name)
                    pod.metadata.namespace = "NA" if pod.metadata.namespace is None else pod.metadata.namespace
                    namespace = pod.metadata.namespace[0:trunk_len_mid] + ".." if len(
                        pod.metadata.namespace) > trunk_len_mid else pod.metadata.namespace
                    pod_name = pod.metadata.name[0:trunk_len_big] + ".." if len(
                        pod.metadata.name) > trunk_len_big else pod.metadata.name
                    nominated_node_name = "<None>" if pod.status.nominated_node_name is None else pod.status.nominated_node_name
                    readiness_gates = "<None>" if pod.spec.readiness_gates is None else pod.spec.readiness_gates
                    pod.status.phase = "NA" if pod.status.phase is None else pod.status.phase
                    restart_count = pod.status.container_statuses[0].restart_count
                    restart_count = "NA" if restart_count is None else restart_count
                    pod.status.pod_ip = "NA" if pod.status.pod_ip is None else pod.status.pod_ip
                    pod.spec.node_name = "NA" if pod.spec.node_name is None else pod.spec.node_name
                    Logger.avail_info(
                        self.PODS_LIST_DISPLAY_FORMAT.format(namespace, pod_name, pod.status.phase, restart_count
                                                             , pod.status.pod_ip,
                                                             pod.spec.node_name,
                                                             nominated_node_name, readiness_gates))
        except ApiException as api_error:
            Logger.err(api_error)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            Logger.err(self.MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER)
        return result_pods_list

    def describe_k8s_pod(self, pod_name):
        # describe pod
        try:
            api_response = self.api_instance.read_namespaced_pod(name=pod_name, namespace='default')
            Logger.info(str(api_response))
            event_details = self.api_instance.list_namespaced_event(namespace='default',
                                                                    field_selector=f'involvedObject.name={pod_name}')
            Logger.sub_info(str(event_details))
        except ApiException as api_error:
            Logger.err(api_error)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            Logger.err(self.MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER)

    def create_k8s_pod(self, file_name, deployment_name):
        # create a pod using yaml file
        try:
            with open(path.join(path.dirname(__file__), file_name)) as f:
                dep = yaml.safe_load(f)
                if deployment_name is not None and len(deployment_name) != 0:
                    dep['metadata']['name'] = deployment_name
                resp = self.apps_api_instance.create_namespaced_deployment(
                    body=dep, namespace="default")
                Logger.info(self.MSG_INFO_POD_CREATED.format(resp.metadata.name))
        except ApiException as api_error:
            Logger.err(api_error)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            Logger.err(self.MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER)

    def list_k8s_deployments(self):
        # list deployments
        try:
            result_deployment_list = []
            deployment_list = self.apps_api_instance.list_namespaced_deployment(namespace="default")
            deployments = deployment_list.items
            if deployments is None or len(deployments) == 0:
                Logger.warn(self.MSG_WARN_NO_DEPLOYMENT.format(""))
                return result_deployment_list
            else:
                Logger.header(self.DEPLOYMENT_HEADER)
                Logger.sub_info(self.DEPLOYMENT_LIST_HEADER_DISPLAY_FORMAT.format("Available"))
                trunk_len_big = 31
                for deployment in deployments:
                    deployment.metadata.name = "NA" if deployment.metadata.name is None else deployment.metadata.name
                    result_deployment_list.append(deployment.metadata.name)
                    deployment.status.ready_replicas = "NA" if deployment.status.ready_replicas is None else deployment.status.ready_replicas
                    deployment.status.replicas = "NA" if deployment.status.replicas is None else deployment.status.replicas
                    deployment.status.updated_replicas = "NA" if deployment.status.updated_replicas is None else deployment.status.updated_replicas
                    deployment.status.available_replicas = "NA" if deployment.status.available_replicas is None else deployment.status.available_replicas
                    deployment.metadata.name = deployment.metadata.name[0:trunk_len_big] + ".." if len(
                        deployment.metadata.name) > trunk_len_big else deployment.metadata.name
                    Logger.avail_info(
                        self.DEPLOYMENT_LIST_DISPLAY_FORMAT.format(deployment.metadata.name,
                                                                   str(deployment.status.ready_replicas) + "/" + str(
                                                                       deployment.status.replicas),
                                                                   deployment.status.updated_replicas,
                                                                   deployment.status.available_replicas))
        except ApiException as api_error:
            Logger.err(api_error)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            Logger.err(self.MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER)
        return result_deployment_list

    def exec_command_on_k8s_pod(self, pod_name, input_cmd):
        # Calling exec and waiting for response
        if input_cmd is not None and len(input_cmd) != 0:
            cmd = input_cmd
            Logger.info("Input CMD:" + str(cmd))
        else:
            cmd = 'echo This message goes to stderr; echo This message goes to stdout'
            Logger.info("Default CMD:" + str(cmd))
        # Calling exec interactively
        exec_command = ['/bin/sh']
        resp = stream(self.api_instance.connect_get_namespaced_pod_exec,
                      pod_name,
                      'default',
                      command=exec_command,
                      stderr=True, stdin=True,
                      stdout=True, tty=False,
                      _preload_content=False)
        commands = [cmd]
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
            if commands:
                c = commands.pop(0)
                print("Running command... %s\n" % c)
                resp.write_stdin(c + "\n")
            else:
                break
        resp.close()

    def deploy_k8s_pod(self, file_name, deployment_name):
        # create a pod using yaml file
        try:
            with open(path.join(path.dirname(__file__), file_name)) as f:
                dep = yaml.safe_load(f)
                if deployment_name is not None and len(deployment_name) != 0:
                    dep['metadata']['name'] = deployment_name
                resp = self.apps_api_instance.create_namespaced_daemon_set(
                    body=dep, namespace="default")
                Logger.info(self.MSG_INFO_POD_DEPLOYED.format(resp.metadata.name))
        except ApiException as api_error:
            Logger.err(api_error)
        except (NewConnectionError, MaxRetryError, ConnectTimeoutError):
            Logger.err(self.MSG_ERR_UNABLE_TO_CONNECT_TO_CLUSTER)
