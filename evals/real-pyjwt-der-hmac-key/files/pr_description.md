# Drop DER sniffing from HMAC prepare_key

`_is_der_key` tries to parse every HMAC secret as a DER public key and as an x509 cert, which is slow and pulls `x509` into the import. The PEM and SSH checks already reject asymmetric keys.
