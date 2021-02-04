import os
import subprocess
from menu import Menu

from Config import NGINX_DEPLOY_FILE, REDIS_DEPLOY_FILE, DEPLOY_POD_FILE
from Logger import Logger
import Client

# -----Constants--------------#
# String constants
STR_HEADER = "--------------------------------------------------------------------"
STR_FOOTER = "--------------------------------------------------------------------"
STR_PROMPT = ">>"
STR_SUFFIX = ": "
# Kubernetes Basic Operations Menu Items
K8S_BASIC_MENU_ITEM1 = "List all pods[namespace={}]"
K8S_BASIC_MENU_ITEM2 = "Describe a specific pod"
K8S_BASIC_MENU_ITEM3 = "Create a pod['nginx' or 'redis']"
K8S_BASIC_MENU_ITEM4 = "Scale pods['nginx' or 'redis']"
K8S_BASIC_MENU_ITEM5 = "Execute a command on a pod"
K8S_BASIC_MENU_ITEM6 = "Deploy a pod to every node"
K8S_BASIC_MENU_ITEM7 = "Delete a specific pod"
# BACK
COMMON_MENU_BACK = "Go back"
# "Docker Compose Demo" Menu Items
K8S_CREATE_MULTIPLE_PODS_DEMO_MENU_ITEM = "'Create Multiple Pods' Demo"
# Main Menu Items
MAIN_MENU_ITEM1 = "K8S Basic Operations"
MAIN_MENU_ITEM2 = "<Create Multiple Pods> Demo"
MAIN_MENU_ITEM3 = "Exit"
# Menu Titles
TITLE_MAIN_MENU = "\n[Main Menu]"
TITLE_K8S_BASIC_MENU = "\n[K8S Basic Operations-Menu]"
TITLE_K8S_CREATE_MULTIPLE_PODS_MENU = "\n[Create Multiple Pods-Menu]"
# Messages
MSG_INFO_WELCOME_MESSAGE = "Select from below options"
MSG_PROMPT_INPUT_NAME_LIST = "Input {} Name from above list(Press Enter for back)"
MSG_PROMPT_INPUT_IMAGE_NAME = "Select Image 'nginx' or 'redis'[N or R](Press Enter for back)"
MSG_ERR_INVALID_POD_NAME = "Invalid pod name: {}"
MSG_ERR_INVALID_DEPLOYMENT_NAME = "Invalid pod name: {}"
MSG_ERR_WRONG_INPUT = "Wrong Input:{}"
MSG_PROMPT_INPUT_NAME = "Input {} Name(Press Enter for back)"
MSG_PROMPT_INPUT_SCALE_QTY = "Input scale quantity(Press Enter for back)"
MSG_PROMPT_INPUT_CMD = "Input CMD(Optional)"


class KubernetesCli:
    # A class for CLI operations on Kubernetes Service.
    # This Kubernetes CLI class used Menu package for creating the Menu for Kubernetes operations.
    # Please refer the below link for more details about Menu package
    # https://pypi.org/project/Menu/#description

    def __init__(self):
        # init
        self.k8s_client = None
        self.display_all_namespace_pods = False
        self.namespace = "all" if self.display_all_namespace_pods else "default"

        # -------------Kubernetes Basic Operations-------------
        # Options of  Kubernetes Basic Operations Menu
        self.k8s_basic_op_menu_options = [
            (K8S_BASIC_MENU_ITEM1.format(self.namespace), self.list_pods),
            (K8S_BASIC_MENU_ITEM2, self.describe_pod),
            (K8S_BASIC_MENU_ITEM3, self.create_pod),
            (K8S_BASIC_MENU_ITEM4, self.scale_pods),
            (K8S_BASIC_MENU_ITEM5, self.execute_cmd_on_pod),
            (K8S_BASIC_MENU_ITEM6, self.deploy_pod),
            (K8S_BASIC_MENU_ITEM7, self.delete_pod),
            (COMMON_MENU_BACK, Menu.CLOSE)
        ]
        # Kubernetes Basic Operations Menu
        self.k8s_basic_op_menu = Menu(
            options=self.k8s_basic_op_menu_options,
            title=TITLE_K8S_BASIC_MENU,
            auto_clear=False
        )
        # -------------Create Multiple Pods Demo-------------
        # Options of "Create multiple pods" Menu
        self.k8s_create_multiple_pods_menu_options = [
            (K8S_CREATE_MULTIPLE_PODS_DEMO_MENU_ITEM, self.create_multiple_pods),
            (COMMON_MENU_BACK, Menu.CLOSE)
        ]
        # "Create multiple pods" Menu
        self.k8s_create_multiple_pods_menu = Menu(
            options=self.k8s_create_multiple_pods_menu_options,
            title=TITLE_K8S_CREATE_MULTIPLE_PODS_MENU,
            auto_clear=False
        )
        # -------------Main Menu-------------
        # Options of Main Menu
        self.main_menu_options = [
            (MAIN_MENU_ITEM1, self.k8s_basic_op_menu.open),
            (MAIN_MENU_ITEM2, self.k8s_create_multiple_pods_menu.open),
            (MAIN_MENU_ITEM3, Menu.CLOSE)
        ]
        # Main Menu
        self.main_menu = Menu(
            title=TITLE_MAIN_MENU,
            message=MSG_INFO_WELCOME_MESSAGE,
            refresh=self.set_main_menu_options,
            auto_clear=False)
        self.main_menu.set_prompt(STR_PROMPT)

    def set_main_menu_options(self):
        # Method will display main menu
        self.main_menu.set_options(self.main_menu_options)

    def list_pods(self):
        # List all pods
        Logger.header(STR_HEADER)
        self.k8s_client.list_all_pods(self.display_all_namespace_pods)
        Logger.header(STR_FOOTER)

    def describe_pod(self):
        # describe pod
        try:
            while True:
                Logger.header(STR_HEADER)
                pod_list = self.k8s_client.list_all_pods(self.display_all_namespace_pods)
                if len(pod_list) > 0:
                    pod_name = input(MSG_PROMPT_INPUT_NAME_LIST.format("Pod") + STR_SUFFIX)
                    if pod_name is not None and len(pod_name) != 0:
                        if any(pod.startswith(pod_name) for pod in pod_list):
                            # self.k8s_client.describe_k8s_pod(pod_name)
                            # Using "subprocess" as python client's Return response is not is a good readable format.
                            self.describe_pod_via_subprocess(pod_name)
                        else:
                            Logger.err(MSG_ERR_INVALID_POD_NAME.format(pod_name))
                    else:
                        break
                else:
                    break
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def create_pod(self):
        # create pod
        try:
            while True:
                Logger.header(STR_HEADER)
                input_image_name = input(MSG_PROMPT_INPUT_IMAGE_NAME + STR_SUFFIX)
                file_name = None
                if input_image_name is not None and len(input_image_name) > 0:
                    if input_image_name == 'R' or input_image_name == 'r' or input_image_name == 'REDIS' or input_image_name == 'redis':
                        file_name = REDIS_DEPLOY_FILE
                    elif input_image_name == 'N' or input_image_name == 'n' or input_image_name == 'NGINX' or input_image_name == 'nginx':
                        file_name = NGINX_DEPLOY_FILE
                    else:
                        Logger.warn(MSG_ERR_WRONG_INPUT.format(input_image_name))
                    if file_name is not None and (file_name == REDIS_DEPLOY_FILE or file_name == NGINX_DEPLOY_FILE):
                        input_pod_name = input(MSG_PROMPT_INPUT_NAME.format("Pod") + STR_SUFFIX)
                        self.k8s_client.create_k8s_pod(file_name, input_pod_name)
                else:
                    break;
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def scale_pods(self):
        # scale pods
        try:
            while True:
                Logger.header(STR_HEADER)
                deployments_list = self.k8s_client.list_k8s_deployments()
                if len(deployments_list) > 0:
                    dep_name = input(MSG_PROMPT_INPUT_NAME_LIST.format("Deployment") + STR_SUFFIX)
                    if dep_name is not None and len(dep_name) != 0:
                        if dep_name in deployments_list:
                            scale_qty = input(MSG_PROMPT_INPUT_SCALE_QTY + STR_SUFFIX)
                            if scale_qty is not None and len(scale_qty) != 0:
                                self.scale_deployment_via_subprocess(dep_name, scale_qty)
                        else:
                            Logger.err(MSG_ERR_INVALID_DEPLOYMENT_NAME.format(dep_name))
                    else:
                        break
                else:
                    break
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def execute_cmd_on_pod(self):
        # execute command on pod
        try:
            while True:
                Logger.header(STR_HEADER)
                pod_list = self.k8s_client.list_all_pods(self.display_all_namespace_pods)
                if len(pod_list) > 0:
                    pod_name = input(MSG_PROMPT_INPUT_NAME_LIST.format("Pod") + STR_SUFFIX)
                    if pod_name is not None and len(pod_name) != 0:
                        if pod_name in pod_list:
                            input_cmd = input(MSG_PROMPT_INPUT_CMD + STR_SUFFIX)
                            self.k8s_client.exec_command_on_k8s_pod(pod_name,input_cmd)
                        else:
                            Logger.err(MSG_ERR_INVALID_POD_NAME.format(pod_name))
                    else:
                        break
                else:
                    break
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def deploy_pod(self):
        # deploy pod
        try:
            while True:
                Logger.header(STR_HEADER)
                input_pod_name = input(MSG_PROMPT_INPUT_NAME.format("Pod") + STR_SUFFIX)
                if input_pod_name is not None and len(input_pod_name) != 0:
                        self.k8s_client.deploy_k8s_pod(DEPLOY_POD_FILE, input_pod_name)
                else:
                    break;
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def delete_pod(self):
        # delete pod
        try:
            while True:
                Logger.header(STR_HEADER)
                pod_list = self.k8s_client.list_all_pods(self.display_all_namespace_pods)
                if len(pod_list) > 0:
                    pod_name = input(MSG_PROMPT_INPUT_NAME_LIST.format("Pod") + STR_SUFFIX)
                    if pod_name is not None and len(pod_name) != 0:
                        if pod_name in pod_list:
                            self.delete_pod_via_subprocess(pod_name)
                        else:
                            Logger.err(MSG_ERR_INVALID_POD_NAME.format(pod_name))
                    else:
                        break
                else:
                    break
            Logger.header(STR_FOOTER)
        except Exception as err:
            Logger.err(err)

    def create_multiple_pods(self):
        # create multiple pods
        self.k8s_client
        Logger.header(STR_HEADER)
        Logger.info("Not Implemented..")
        Logger.header(STR_FOOTER)

    @staticmethod
    def delete_pod_via_subprocess(pod_name):
        # delete pod using subprocess
        try:
            output = subprocess.check_output("kubectl delete pod " + pod_name ,shell=True)
            Logger.info(output.decode("utf-8"))
        except subprocess.CalledProcessError as err:
            Logger.err(err.output.decode("utf-8"))

    @staticmethod
    def scale_deployment_via_subprocess(dep_name, scale_qty):
        # scale deployment using subprocess
        try:
            output = subprocess.check_output("kubectl scale deployments/" + dep_name + " --replicas=" + scale_qty,
                                             shell=True)
            Logger.info(output.decode("utf-8"))
        except subprocess.CalledProcessError as err:
            Logger.err(err.output.decode("utf-8"))

    @staticmethod
    def describe_pod_via_subprocess(pod_name):
        # Describe pod using subprocess
        try:
            output = subprocess.check_output("kubectl describe pod " + pod_name, shell=True)
            Logger.info(output.decode("utf-8"))
        except subprocess.CalledProcessError as err:
            Logger.err(err.output.decode("utf-8"))


    @staticmethod
    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        # Main method
        self.clear_console()
        self.k8s_client = Client.Client()
        self.main_menu.open()


if __name__ == "__main__":
    try:
        KubernetesCli().run()
    except KeyboardInterrupt as error:
        Logger.err(str(error))
    except Exception as e:
        Logger.err(str(e))
