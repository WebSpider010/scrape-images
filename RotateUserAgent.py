import json
import random

class RotateUserAgent:
    used = None
    user_agents = None
    user_agents_file = "user_agents.json"
    used_user_agents = set()
    def load_error(func):
        def warper(*args):
            if RotateUserAgent.user_agents is None:
                print("Load user agents using `load_user_agents`")
                exit(-1)
            return func(*args)
        return warper
        
    @staticmethod
    def set_filepath(filepath):
        RotateUserAgent.user_agents_file = filepath
    @staticmethod
    def load_user_agents():
        with open(RotateUserAgent.user_agents_file, "r") as file:
            RotateUserAgent.user_agents = set(json.load(file))

    @staticmethod
    @load_error
    def get_new(current_user_agent: str=None):
        if current_user_agent:
            RotateUserAgent.used_user_agents.add(current_user_agent)
        for user_agent in RotateUserAgent.user_agents:
            if user_agent not in RotateUserAgent.used_user_agents:
                return user_agent
        print("All user-agents are used")
        return None
    
    @staticmethod
    @load_error
    def get_random():
        user_agent = random.choice(list(RotateUserAgent.user_agents))
        return user_agent
    
    @staticmethod
    @load_error
    def insert(user_agent: str):
        if user_agent in RotateUserAgent.user_agents:
            print(f"User agent {user_agent} already exist")
        RotateUserAgent.user_agents.add(user_agent)

    @staticmethod
    @load_error
    def get_product_names():
        product_names = []
        for user_agent in RotateUserAgent.user_agents:
            product_name = user_agent.split(' ')[0]
            if product_name not in product_names:
                product_names.append(product_name)
        return product_names
            
    @staticmethod
    @load_error
    def get_by_procuct(productname: str):
        user_agents = set()
        for user_agent in RotateUserAgent.user_agents:
            product_name = user_agent.split('/')[0]
            if productname.lower() == product_name.lower():
                user_agents.add(user_agent)
        return user_agents
    
    @staticmethod
    @load_error
    def get_by_platform(platform: str):
        user_agents = []
        platforms = [
            "windows",
            "android",
            "ios",
        ]
        if platform.lower() not in platforms:
            print("Platform not supported")
            return None
        for user_agent in RotateUserAgent.user_agents:
            if platform in user_agent.lower():
                user_agents.append(user_agent)
        return user_agents
    
if __name__ == "__main__":
    #load the user agents
    RotateUserAgent.load_user_agents()
    # Get by product name like 'Mozilla'
    #print("#"*10, "Get by product name", "#"*10)
    #print(RotateUserAgent.get_by_procuct("Mozilla"))
    # Get by platform
    #print("#"*10, "Get by platform", "#"*10)
    #print(RotateUserAgent.get_by_platform("windows"))
    
    

