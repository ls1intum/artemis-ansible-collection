import subprocess
import argparse

HOST_TYPES = ["node", "agent", "db", "broker", "proxy", "storage"]

# Used for the ipv6 address generation. (e.g. broker -> ::b:1)
HOST_TYPE_NETWORKS = ["a", "affe", "d", "b", "f", "9"]

MAPPPING = dict(zip(HOST_TYPES, HOST_TYPE_NETWORKS))


def gen_key():
    privkey = subprocess.check_output(
        "wg genkey", shell=True).decode("utf-8").strip()
    pubkey = subprocess.check_output(
        f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
    return (pubkey, privkey)


def store_host_var_file(pub, priv, h_type, host_id, filename):
    print(pub, priv, host_id, filename)

    content = f"""
# IPv6 address (with CIDR!) which can be used to access the node - If left blank, ansible will use host facts to fill the address.
wireguard_host_ipv6_address:
host_ipv4_address:

# Address of the node inside the network.
wireguard_interface_address: "fcfe:0:0:0:0:0:{MAPPPING[h_type]}:{host_id}"

# Wireguard Keys - Autmatically generated!
wireguard_pubkey: {pub}
wireguard_privkey: {priv}
"""

    if h_type == "node":
        content += f"\nnode_id: {host_id}\n"

    if h_type == "agent":
        content += f"\nnode_id: 1{host_id:03d}\n"
        content += f"node_short_name: artemis-build-agent-{host_id}\n"
        content += f"node_display_name: Artemis Build Agent {host_id}\n"

    with open(f"{filename}.yml", 'w') as f:
        f.writelines(content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate ansible host_vars for artemis wireguard role")

    # Add arguments for each HOST_TYPES entry:
    for h_type in HOST_TYPES:
        parser.add_argument(f"--{h_type}", type=int, default=1,
                            help=f"Number of {h_type} nodes to generate")

    parser.add_argument('--hostprefix', type=str, required=True,
                        help="Hostname prefix which is used to generate host_var files. (e.g. artemis_ -> artemis_proxy, artemis_node1)")

    parser.add_argument('--hostsuffix', type=str, required=True,
                        help="Hostname suffix which is used to generate host_var files. (e.g. .test.com -> proxy.test.com, node1.test.com)")

    args = vars(parser.parse_args())

    prefix = args['hostprefix']
    suffix = args['hostsuffix']

    # Iterate over all host types
    for h_type in HOST_TYPES:

        number_of_nodes = args[h_type]

        # Check how many nodes have to be created - If only one node is needed omit id
        if number_of_nodes > 1:
            # Iterate over number of nodes in current type
            for i in range(number_of_nodes):

                pub, priv = gen_key()
                store_host_var_file(pub, priv, h_type, i + 1,
                                    prefix + h_type + str(i + 1) + suffix)
        else:
            pub, priv = gen_key()
            store_host_var_file(pub, priv, h_type, 1, prefix + h_type + suffix)

    print("Files Written")


main()
