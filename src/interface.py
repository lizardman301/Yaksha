#!/usr/bin/python
'''
Module that functions as an interface between the commands and the irc/discord
libaries. Provides a common inteface that allows the commands to function the
same regardless of which version of the bot is instantiated.

There are two main components to the interface class. remap_functions which
creates a dictionary of commands and the functions and call_command which
handles each valid command received by the bot. 
'''
from commands import ifgc, voting, actions
from commands import utilities
import re

class Interface():

    def __init__(self, config, bot_commands):
        self._func_mapping = {}
        self._class_mapping = {}
        self.no_cache_pattern = r'--nocache'
        self._modules = [ifgc, voting, actions]
        self.config = config
        self.registered_commands = bot_commands

        self.remap_functions()

    def remap_functions(self):
        '''
        Utilities.get_callbacks() returns a dictionary mapping of
        each command with the name of the function to be called.

        The name of the function is replaced by this function
        with a reference to the function and the class it belongs
        to. This is later used by self.call_command when handling 
        messages.
        '''
        name_mapping = utilities.get_callbacks()

        for key, value in name_mapping.items():
            class_name, func_name = value[0].split('.')
            module_name = value[1]
            # Go through the imported modules to determine which
            # module the class belongs to.
            for module in self._modules:
                if module.__name__ != module_name:
                    continue
                else:
                    class_ref = getattr(module, class_name)
                    func_ref = getattr(class_ref, func_name)

                    # Check if we already have a reference to
                    # this class and add it if not.
                    if class_name not in self._class_mapping:
                        self._class_mapping[class_name] = class_ref

                    # Replace the function name with a tuple
                    # containing a reference to the function and
                    # the class name. The class name will be used
                    # get the correct class from self._class_mapping.
                    self._func_mapping[key] = (func_ref, class_name)

                    # We found the module so there is no need for further
                    # iterations.
                    break

        # Go through the class mapping and replace references to the classes
        # with their instances.
        for name, instance in self._class_mapping.items():
            self._class_mapping[name] = instance(self.config)

    async def call_command(self, command, msg, *args, **kwargs):
        '''
        Determines which function to call from the func_mapping
        dict using the command arg as the key.
        Also allows you to 'refresh' the cache by passing '--nocache' in 
        the message.
        '''
        func, class_name = self._func_mapping[command]
        # Check if we shouldn't use the cache.
        if re.search(self.no_cache_pattern, msg):
            msg = re.sub(self.no_cache_pattern, '', msg).strip()
            kwargs.update({'no_cache': True})

        # Special case if its the help command that requires you
        # to pass in the available commands.
        if command == '?help':
            kwargs['commands_dict'] = self.registered_commands
        # Call the actual function passing the instance of the
        # class as the first argument.
        return await func(self._class_mapping[class_name], msg,
                          *args, **kwargs)
