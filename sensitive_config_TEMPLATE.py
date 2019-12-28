""" sensitive_config_TEMPLATE.py:

      the below generated with securityCodes.py
      but a rather good random is easily usable from Ansible as a shell call:

      python3 -c "import os; multiURandomInt=lambda: sum(256**i * b for \
          i,b in enumerate(os.urandom(2))); \
          skChars=list('1234567890poiuytrewqasdfghjklkmnbvcxz'); \
          print(''.join((skChars[multiURandomInt() % \
          len(skChars)]) for _ in range(48)))"
"""

# SECRET_KEY = 'insert_a_very_unguessable_48char_secret_key_here'
