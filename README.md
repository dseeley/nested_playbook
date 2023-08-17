# Ansible Collection - dseeley.nested_playbook

An Ansible action plugin to include (nest) a playbook.  This literally runs a playbook in a subprocess; the subprocess playbook takes no environment, extra variables etc. from, (nor returns any to) the parent playbook.

(This is quite different from the operation of ansible.builtin.import_playbook).

## Execution

Create a playbook file to be called from within another, e.g:`test_nested.yml`:
```yaml
- name: test
  hosts: localhost
  gather_facts: no
  tasks:
    - debug: msg="Child playbook - 1"

    - ansible.builtin.pause:
        seconds: 1

    - debug: msg="Child playbook - 2"

    - fail: msg="testfail=fail"
      when: testfail is defined and testfail == "fail"
```

Create the parent file.  Either: `test_parent__cmdline.yml`:
```yaml
- name: test
  hosts: localhost
  gather_facts: no
  tasks:
    - debug: msg="Parent playbook"

    - name: Execute nested Playbook
      dseeley.nested_playbook.nested_playbook:
        playbook_cmdline: './test_nested.yml -e test=true'
        indent: 12
```

or: `test_parent__args.yml`:
```yaml
- name: test
  hosts: localhost
  gather_facts: no
  tasks:
    - debug: msg="Parent playbook"

    - name: Execute nested Playbook
      dseeley.nested_playbook.nested_playbook:
        playbook_path: './test_nested.yml'
        playbook_args: ['-e', 'test=true']
```

Execute:
```
ansible-playbook test_parent__args.yml
ansible-playbook test_parent__cmdline.yml
```
