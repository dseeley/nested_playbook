# Copyright 2023 Dougal Seeley <github@dougalseeley.com>
# BSD 3-Clause License

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
import __main__
import subprocess
import os
import pty
import shlex

display = Display()

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        ansible_executable = __main__.__file__

        # Get the command line arguments from the task
        playbook_args = self._task.args.get('playbook_args', [])
        playbook_path = self._task.args.get('playbook_path', None)
        playbook_cmdline = self._task.args.get('playbook_cmdline', None)
        indent_prefix = self._task.args.get('indent', 8) * " "

        if not (playbook_cmdline or playbook_path):
            result['failed'] = True
            result['msg'] = f"Either playbook_cmdline or playbook_path is required"
        elif type(playbook_args) != list:
            result['failed'] = True
            result['msg'] = f"playbook_args must be a list"
        else:
            if playbook_cmdline:
                command = [ansible_executable] + playbook_args + shlex.split(playbook_cmdline)
            else:
                command = [ansible_executable] + playbook_args + [playbook_path]

            try:
                # Create a pseudo-terminal pair (pty) to execute the playbook
                master, slave = pty.openpty()

                # Use subprocess to execute the playbook and capture both stdout and stderr
                process = subprocess.Popen(command, stdout=slave, stderr=slave, text=True, close_fds=True)

                # Close the slave end of the pty in the parent process
                os.close(slave)

                output_str = indent_prefix + "NESTED PLAYBOOK [" + str(command) + "]\n"

                while process.poll() is None:
                    try:
                        nested_playbook_return = os.read(master, 4096).decode('utf-8', errors='replace')
                        if nested_playbook_return:
                            output_str += "\n".join(indent_prefix + line for line in nested_playbook_return.splitlines()) + "\n"
                            print(output_str, end='', flush=True)
                            output_str = ""
                    except OSError as e:
                        if e.errno == 5:  # Input/output error - ignore this as it results from reading from the file descriptor after it has closed itself (i.e. the playbook has finished)
                            pass
                        else:
                            raise  # Reraise other OSError exceptions

                if process.returncode != 0:
                    result['failed'] = True
                    result['msg'] = f"Playbook execution failed with return code {process.returncode}"
            except Exception as e:
                result['failed'] = True
                result['msg'] = str(e)
            finally:
                # Close the master end of the pty
                os.close(master)

        return result
