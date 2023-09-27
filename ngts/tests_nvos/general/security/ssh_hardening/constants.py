class SshHardeningConsts:
    TIMEOUT = 3

    PROTOCOL = 'protocol'
    COMPRESSION = 'compression'
    CIPHERS = 'ciphers'
    MACS = 'MACs'
    KEX_ALGOS = 'kex-algorithms'

    OPTIONS_FOR_FUNCTIONAL_TEST = [CIPHERS, MACS, KEX_ALGOS]

    VALUES = {
        PROTOCOL: '2.0',
        COMPRESSION: 'none',
        CIPHERS: ['aes256-ctr', 'aes192-ctr', 'aes128-ctr', 'aes128-gcm@openssh.com', 'aes256-gcm@openssh.com'],
        MACS: ['hmac-sha2-256', 'hmac-sha2-512', 'hmac-sha2-512-etm@openssh.com', 'hmac-sha2-256-etm@openssh.com'],
        KEX_ALGOS: ['curve25519-sha256', 'curve25519-sha256@libssh.org', 'diffie-hellman-group16-sha512',
                    'diffie-hellman-group18-sha512', 'diffie-hellman-group14-sha256']
    }

    DEFAULTS = {
        CIPHERS: ['3des-cbc',
                  'aes128-cbc',
                  'aes192-cbc',
                  'aes256-cbc',
                  'rijndael-cbc@lysator.liu.se',
                  'aes128-ctr',
                  'aes192-ctr',
                  'aes256-ctr',
                  'aes128-gcm@openssh.com',
                  'aes256-gcm@openssh.com',
                  'chacha20-poly1305@openssh.com'
                  ],
        MACS: ['hmac-sha1',
               'hmac-sha1-96',
               'hmac-sha2-256',
               'hmac-sha2-512',
               'hmac-md5',
               'hmac-md5-96',
               'umac-64@openssh.com',
               'umac-128@openssh.com',
               'hmac-sha1-etm@openssh.com',
               'hmac-sha1-96-etm@openssh.com',
               'hmac-sha2-256-etm@openssh.com',
               'hmac-sha2-512-etm@openssh.com',
               'hmac-md5-etm@openssh.com',
               'hmac-md5-96-etm@openssh.com',
               'umac-64-etm@openssh.com',
               'umac-128-etm@openssh.com'
               ],
        KEX_ALGOS: ['diffie-hellman-group1-sha1',
                    'diffie-hellman-group14-sha1',
                    'diffie-hellman-group14-sha256',
                    'diffie-hellman-group16-sha512',
                    'diffie-hellman-group18-sha512',
                    'diffie-hellman-group-exchange-sha1',
                    'diffie-hellman-group-exchange-sha256',
                    'ecdh-sha2-nistp256',
                    'ecdh-sha2-nistp384',
                    'ecdh-sha2-nistp521',
                    'curve25519-sha256',
                    'curve25519-sha256@libssh.org',
                    # 'sntrup4591761x25519-sha512@tinyssh.org'
                    ]
    }

    SSH_CMD_FLAGS = {
        CIPHERS: '-c ',
        MACS: '-m ',
        KEX_ALGOS: '-o KexAlgorithms='
    }

    ERROR_PATTERN_PREFIX = 'Unable to negotiate with.*'
    ERROR_PATTERNS = {
        CIPHERS: rf'{ERROR_PATTERN_PREFIX} no matching cipher found.',
        MACS: rf'{ERROR_PATTERN_PREFIX} no matching MAC found.',
        KEX_ALGOS: rf'{ERROR_PATTERN_PREFIX} no matching key exchange method found.'
    }
