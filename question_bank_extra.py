from __future__ import annotations


EXTRA_QUESTION_BANK = {
    "CCNA": {
        "Network Fundamentals": [
            {
                "concept": "ARP",
                "correct": "ARP maps an IPv4 address to a MAC address on the local network segment.",
                "distractors": [
                    "ARP assigns default gateways to remote routers automatically.",
                    "ARP encrypts Ethernet frames before they cross a trunk.",
                    "ARP advertises dynamic routes between autonomous systems.",
                ],
                "explanation": "Hosts use ARP when they know the target IPv4 address but need the Layer 2 destination for local delivery.",
                "summary": ["ARP resolves local IPv4-to-MAC mappings.", "It matters before the first local frame can be sent."],
                "key_terms": ["ARP", "IPv4", "MAC address", "local segment"],
                "memory_tip": "IP in hand, MAC still needed.",
            },
            {
                "concept": "subnet mask",
                "correct": "A subnet mask identifies which bits of an IPv4 address belong to the network and which belong to the host.",
                "distractors": [
                    "A subnet mask is used only to encrypt packets before routing.",
                    "A subnet mask assigns default gateways through the DNS service.",
                    "A subnet mask controls PoE wattage on an access switch.",
                ],
                "explanation": "Hosts use the mask to decide whether traffic is local or must be sent to a router.",
                "summary": ["Masks define the network boundary.", "Local-versus-remote decisions depend on the mask."],
                "key_terms": ["subnet mask", "IPv4", "network boundary", "host portion"],
                "memory_tip": "Mask first, then decide whether the router is needed.",
            }
        ],
        "Network Access": [
            {
                "concept": "port security",
                "correct": "Port security limits which MAC addresses can use a switchport and can react when violations occur.",
                "distractors": [
                    "Port security dynamically creates OSPF neighbors on access ports.",
                    "Port security routes traffic between VLANs without a Layer 3 device.",
                    "Port security replaces spanning tree on redundant links.",
                ],
                "explanation": "It is a common access-layer hardening feature for reducing unauthorized device attachment.",
                "summary": ["Port security constrains MAC learning on a port.", "Violation actions can protect the access layer."],
                "key_terms": ["port security", "MAC limit", "violation", "switchport"],
                "memory_tip": "Lock the port before the rogue host lands.",
            }
        ],
        "IP Connectivity": [
            {
                "concept": "default route",
                "correct": "A default route is used when no more specific route exists in the routing table.",
                "distractors": [
                    "A default route is required only for traffic inside the same VLAN.",
                    "A default route automatically replaces all dynamic routing protocols.",
                    "A default route exists only in ARP caches, not routing tables.",
                ],
                "explanation": "The default route is the catch-all path for unknown destinations.",
                "summary": ["Default routes handle anything not otherwise matched.", "They are common at network edges."],
                "key_terms": ["default route", "routing table", "gateway of last resort"],
                "memory_tip": "Unknown destination means use the escape path.",
            }
        ],
        "IP Services": [
            {
                "concept": "DNS",
                "correct": "DNS resolves human-readable names into records such as IP addresses.",
                "distractors": [
                    "DNS rewrites source ports for internet-bound sessions.",
                    "DNS prevents switching loops in a campus topology.",
                    "DNS provides DHCP leases for wireless clients.",
                ],
                "explanation": "DNS is a foundational service because users and applications depend on names more often than raw IP addresses.",
                "summary": ["Name resolution is a daily network dependency.", "When DNS fails, healthy services can still feel offline."],
                "key_terms": ["DNS", "name resolution", "record", "hostname"],
                "memory_tip": "If names break, users think the network is down.",
            }
        ],
        "Security Fundamentals": [
            {
                "concept": "VPN",
                "correct": "A VPN protects data in transit by creating an encrypted tunnel across an untrusted network.",
                "distractors": [
                    "A VPN replaces every need for endpoint authentication.",
                    "A VPN changes MAC addresses to route between VLANs.",
                    "A VPN exists only for local switch management over console cables.",
                ],
                "explanation": "VPNs are used to extend secure connectivity over public or shared transport.",
                "summary": ["Encryption in transit matters beyond the office LAN.", "Tunnels protect the path, not weak credentials."],
                "key_terms": ["VPN", "tunnel", "encryption", "remote access"],
                "memory_tip": "Secure path, still need secure identities.",
            }
        ],
        "Automation & Programmability": [
            {
                "concept": "configuration management",
                "correct": "Configuration management tools reduce drift by applying consistent desired state across many devices.",
                "distractors": [
                    "Configuration management removes the need for IP addressing plans.",
                    "Configuration management is used only for physical cable labeling.",
                    "Configuration management replaces routing adjacencies with static MAC tables.",
                ],
                "explanation": "Automation is valuable because consistency is hard to maintain manually at scale.",
                "summary": ["Desired state beats one-off CLI snowflakes.", "Automation reduces inconsistency over time."],
                "key_terms": ["configuration management", "desired state", "drift", "automation"],
                "memory_tip": "Scale breaks manual discipline first.",
            }
        ],
    },
    "AZ-900": {
        "Cloud Concepts": [
            {
                "concept": "high availability",
                "correct": "High availability is the design goal of keeping workloads accessible despite component failures.",
                "distractors": [
                    "High availability means using a single oversized server for simplicity.",
                    "High availability removes the need for backup and recovery planning.",
                    "High availability applies only to on-premises hardware refresh cycles.",
                ],
                "explanation": "Cloud platforms provide building blocks, but workload design still determines resilience.",
                "summary": ["Availability is engineered, not assumed.", "Redundancy matters only when failover works."],
                "key_terms": ["high availability", "resilience", "failover", "redundancy"],
                "memory_tip": "Redundant parts are only useful if the service survives the fault.",
            },
            {
                "concept": "OpEx vs CapEx",
                "correct": "Operational expenditure is a recurring cost model, while capital expenditure is usually an upfront investment in owned assets.",
                "distractors": [
                    "OpEx and CapEx are Azure services used only for data encryption.",
                    "OpEx applies only to networking hardware and CapEx applies only to identity systems.",
                    "OpEx and CapEx describe two types of virtual machine backup snapshots.",
                ],
                "explanation": "Cloud discussions often compare recurring service spending with traditional infrastructure purchase models.",
                "summary": ["Cloud consumption often feels like OpEx.", "Buying hardware outright is a classic CapEx example."],
                "key_terms": ["OpEx", "CapEx", "cloud economics", "consumption"],
                "memory_tip": "Renting often looks like OpEx. Owning often looks like CapEx.",
            }
        ],
        "Core Azure Services": [
            {
                "concept": "Azure Virtual Network",
                "correct": "Azure Virtual Network provides isolated networking for Azure resources, including subnets and routing controls.",
                "distractors": [
                    "Azure Virtual Network is used only for SaaS identity licensing.",
                    "Azure Virtual Network replaces Microsoft Entra ID authentication policies.",
                    "Azure Virtual Network stores blob data as a backup archive service.",
                ],
                "explanation": "Virtual networking is the foundation for secure connectivity between Azure resources.",
                "summary": ["Compute needs network boundaries.", "Subnets and routing shape workload placement."],
                "key_terms": ["VNet", "subnet", "routing", "network isolation"],
                "memory_tip": "Cloud resources still need a network map.",
            }
        ],
        "Azure Management & Governance": [
            {
                "concept": "resource groups",
                "correct": "A resource group is a logical container for Azure resources that share lifecycle or management context.",
                "distractors": [
                    "A resource group replaces subscriptions in tenant billing.",
                    "A resource group is used only to host identity federation metadata.",
                    "A resource group automatically performs OS patching inside virtual machines.",
                ],
                "explanation": "Resource groups make deployment, permissions, and organization easier within a subscription.",
                "summary": ["Group resources by lifecycle and management needs.", "They are operational containers, not network boundaries."],
                "key_terms": ["resource group", "lifecycle", "Azure", "management"],
                "memory_tip": "Group by how you manage and retire, not by guesswork.",
            }
        ],
        "Identity & Security": [
            {
                "concept": "role-based access control",
                "correct": "Role-based access control grants permissions based on assigned roles instead of ad hoc per-user settings.",
                "distractors": [
                    "Role-based access control replaces encryption at rest.",
                    "Role-based access control is used only for storage account replication.",
                    "Role-based access control disables least privilege by default.",
                ],
                "explanation": "RBAC improves security and manageability by aligning permissions to job function.",
                "summary": ["RBAC scales cleaner than one-off permissions.", "Least privilege works better with role design."],
                "key_terms": ["RBAC", "least privilege", "role assignment", "authorization"],
                "memory_tip": "Grant the role, not the random exception.",
            }
        ],
    },
    "AZ-800": {
        "Hybrid Identity": [
            {
                "concept": "single sign-on",
                "correct": "Single sign-on reduces repeated authentication prompts by letting trusted identity services issue reusable access decisions.",
                "distractors": [
                    "Single sign-on stores every credential in shared plain text for convenience.",
                    "Single sign-on replaces all directory synchronization needs.",
                    "Single sign-on is used only for DHCP failover pairs.",
                ],
                "explanation": "SSO improves user experience while still depending on strong identity controls behind the scenes.",
                "summary": ["SSO reduces friction, not the need for security.", "Trust flow design matters."],
                "key_terms": ["SSO", "authentication", "trust", "identity"],
                "memory_tip": "Fewer prompts should not mean weaker control.",
            },
            {
                "concept": "password hash synchronization",
                "correct": "Password hash synchronization lets users authenticate to cloud resources with identity data synced from on-premises Active Directory.",
                "distractors": [
                    "Password hash synchronization copies clear-text passwords into every cloud workload.",
                    "Password hash synchronization eliminates all need for multifactor authentication.",
                    "Password hash synchronization is used only to replicate DHCP scopes.",
                ],
                "explanation": "It is a common hybrid identity design because it simplifies sign-in while integrating cloud identity.",
                "summary": ["Hybrid sign-in often depends on synced credential data.", "Design choices affect user experience and risk."],
                "key_terms": ["password hash sync", "hybrid identity", "Entra ID", "authentication"],
                "memory_tip": "Sync the auth signal, not the clear text secret.",
            }
        ],
        "Windows Server Administration": [
            {
                "concept": "Windows Admin Center",
                "correct": "Windows Admin Center provides browser-based management for Windows Server infrastructure.",
                "distractors": [
                    "Windows Admin Center is a replacement for NTFS permissions.",
                    "Windows Admin Center assigns DNS records only through command-line routing commands.",
                    "Windows Admin Center exists solely for Linux package repositories.",
                ],
                "explanation": "It gives administrators a modern interface for common server management tasks.",
                "summary": ["Browser-based admin improves access to common tasks.", "It complements, not replaces, automation."],
                "key_terms": ["Windows Admin Center", "browser management", "server admin"],
                "memory_tip": "Modern admin UI, same need for disciplined operations.",
            }
        ],
        "Active Directory": [
            {
                "concept": "FSMO roles",
                "correct": "FSMO roles are specialized Active Directory operations that must be handled by specific domain controllers.",
                "distractors": [
                    "FSMO roles define wireless encryption channels on domain-joined laptops.",
                    "FSMO roles are file share permissions applied to every OU.",
                    "FSMO roles replace DNS zones for service discovery.",
                ],
                "explanation": "Some AD tasks cannot be multi-master and are assigned to role holders.",
                "summary": ["Certain directory operations need a single authority.", "Knowing role placement helps troubleshooting."],
                "key_terms": ["FSMO", "domain controller", "AD roles", "operations master"],
                "memory_tip": "Some AD jobs need one referee, not many.",
            }
        ],
        "File & Storage": [
            {
                "concept": "share permissions",
                "correct": "Share permissions control network access to shared folders and combine with NTFS permissions for effective access.",
                "distractors": [
                    "Share permissions replace disk redundancy technologies like mirroring.",
                    "Share permissions assign IP gateways to Windows clients.",
                    "Share permissions are used only for forest trust authentication.",
                ],
                "explanation": "Effective file access is shaped by both share-level and file-system-level permission models.",
                "summary": ["Share gets you through the door.", "NTFS determines what you can do once inside."],
                "key_terms": ["share permissions", "NTFS", "effective access", "SMB"],
                "memory_tip": "Network entry and file rights are not the same control.",
            }
        ],
        "Networking": [
            {
                "concept": "IPAM",
                "correct": "IP Address Management centralizes visibility and administration for address space, DHCP, and DNS data.",
                "distractors": [
                    "IPAM is used only to encrypt disk volumes on branch servers.",
                    "IPAM replaces Active Directory delegation models.",
                    "IPAM is a browser theme for Windows Admin Center.",
                ],
                "explanation": "As environments grow, address planning and service visibility get harder without central control.",
                "summary": ["IPAM reduces address chaos.", "DNS and DHCP insight matter as much as raw subnets."],
                "key_terms": ["IPAM", "DHCP", "DNS", "address management"],
                "memory_tip": "If addresses drift, troubleshooting slows down.",
            }
        ],
        "Security": [
            {
                "concept": "Just Enough Administration",
                "correct": "Just Enough Administration limits administrative capabilities to only the commands or tasks required.",
                "distractors": [
                    "Just Enough Administration means every admin uses unrestricted local administrator rights.",
                    "Just Enough Administration is a file replication technology for DFS.",
                    "Just Enough Administration disables auditing for privileged sessions.",
                ],
                "explanation": "JEA reduces risk by narrowing privileged operations instead of handing out broad admin rights.",
                "summary": ["Privilege should be scoped by task, not title alone.", "Admin sessions need tighter blast-radius control."],
                "key_terms": ["JEA", "least privilege", "PowerShell", "role capability"],
                "memory_tip": "Give only the commands, not the kingdom.",
            }
        ],
        "Monitoring & Recovery": [
            {
                "concept": "recovery objectives",
                "correct": "RPO and RTO define how much data loss is tolerable and how quickly service must be restored.",
                "distractors": [
                    "RPO and RTO are Active Directory trust attributes.",
                    "RPO and RTO are DHCP scope reservation settings.",
                    "RPO and RTO control NTFS inheritance on shared folders.",
                ],
                "explanation": "Recovery strategy has to match business tolerance for downtime and lost transactions.",
                "summary": ["Recovery targets drive backup design.", "Not every workload needs the same restore speed."],
                "key_terms": ["RPO", "RTO", "recovery", "business impact"],
                "memory_tip": "Know how much loss and delay the business can actually survive.",
            }
        ],
    },
    "Security+": {
        "General Security Concepts": [
            {
                "concept": "least privilege",
                "correct": "Least privilege reduces risk by granting only the access required for the current role or task.",
                "distractors": [
                    "Least privilege requires every administrator to share one common root account.",
                    "Least privilege eliminates the need for logging and review.",
                    "Least privilege applies only to physical security badges, not digital access.",
                ],
                "explanation": "Excess permissions expand blast radius when accounts are compromised or misused.",
                "summary": ["Smaller access boundaries mean smaller failures.", "Privilege should be temporary and intentional."],
                "key_terms": ["least privilege", "access control", "blast radius", "permissions"],
                "memory_tip": "Enough access wins. Extra access leaks.",
            },
            {
                "concept": "non-repudiation",
                "correct": "Non-repudiation provides evidence that an action can be tied to a specific party so it cannot be credibly denied later.",
                "distractors": [
                    "Non-repudiation is the process of hiding a server behind NAT.",
                    "Non-repudiation means every account automatically receives admin rights.",
                    "Non-repudiation replaces service availability planning during outages.",
                ],
                "explanation": "Digital signatures, trustworthy logs, and strong identity controls commonly support non-repudiation.",
                "summary": ["You need proof of who performed the action.", "Identity plus evidence makes later review defensible."],
                "key_terms": ["non-repudiation", "digital signature", "accountability", "evidence"],
                "memory_tip": "If it matters later, leave proof now.",
            }
        ],
        "Threats & Vulnerabilities": [
            {
                "concept": "patch management",
                "correct": "Patch management reduces exposure by applying vendor fixes in a controlled and timely way.",
                "distractors": [
                    "Patch management is used only to rotate physical badge access.",
                    "Patch management guarantees systems never fail after updates.",
                    "Patch management replaces asset inventories and vulnerability scans.",
                ],
                "explanation": "Timely remediation matters, but patching still needs validation and change control.",
                "summary": ["Unpatched systems carry avoidable risk.", "Fast patching without discipline can create outages."],
                "key_terms": ["patching", "remediation", "change control", "exposure"],
                "memory_tip": "Fix fast, but not blindly.",
            }
        ],
        "Security Architecture": [
            {
                "concept": "secure network design",
                "correct": "Secure network design uses layered controls such as segmentation, filtering, and controlled trust boundaries.",
                "distractors": [
                    "Secure network design means putting every system on one flat trusted subnet.",
                    "Secure network design removes the need for endpoint hardening.",
                    "Secure network design is focused only on password length settings.",
                ],
                "explanation": "Architecture matters because control placement shapes how far an attacker can move.",
                "summary": ["Security should exist in the paths between systems, not just on the endpoints.", "Trust boundaries need to be intentional."],
                "key_terms": ["architecture", "segmentation", "trust boundary", "filtering"],
                "memory_tip": "Design the lanes before traffic shows up.",
            }
        ],
        "Security Operations": [
            {
                "concept": "playbooks",
                "correct": "Playbooks give responders repeatable steps for handling common incidents consistently under pressure.",
                "distractors": [
                    "Playbooks replace the need for evidence preservation.",
                    "Playbooks are used only for procurement approvals.",
                    "Playbooks permanently eliminate analyst judgment during investigations.",
                ],
                "explanation": "A good playbook improves speed and consistency without replacing critical thinking.",
                "summary": ["Repeatable response beats improvised chaos.", "Analysts still need judgment inside the process."],
                "key_terms": ["playbook", "incident response", "workflow", "consistency"],
                "memory_tip": "Pressure is not the time to invent the process.",
            }
        ],
        "Governance & Risk": [
            {
                "concept": "data classification",
                "correct": "Data classification labels information by sensitivity so controls can match business and legal requirements.",
                "distractors": [
                    "Data classification is the process of assigning IP subnets to branch offices.",
                    "Data classification replaces encryption key management.",
                    "Data classification is used only for hardware asset disposal.",
                ],
                "explanation": "You cannot protect information well if you do not know what is sensitive and why.",
                "summary": ["Protection should follow data value and sensitivity.", "Classification makes control priorities clearer."],
                "key_terms": ["data classification", "sensitivity", "handling", "governance"],
                "memory_tip": "Know what matters before you decide how hard to guard it.",
            }
        ],
    },
    "Network+": {
        "Networking Concepts": [
            {
                "concept": "default gateway",
                "correct": "A default gateway is the local router interface a host uses to reach remote networks.",
                "distractors": [
                    "A default gateway is the DNS server that resolves all internet hostnames.",
                    "A default gateway is the switchport that powers a wireless access point.",
                    "A default gateway is the MAC address of the local NIC burned into hardware.",
                ],
                "explanation": "Hosts need a next-hop device when the destination is outside the local subnet.",
                "summary": ["Remote traffic needs a router exit point.", "Local traffic does not require the gateway."],
                "key_terms": ["default gateway", "router", "subnet", "next hop"],
                "memory_tip": "Off-subnet means go to the router.",
            },
            {
                "concept": "DNS caching",
                "correct": "DNS caching speeds repeated lookups by storing recently resolved records for a limited time based on their TTL.",
                "distractors": [
                    "DNS caching permanently overrides all authoritative DNS updates.",
                    "DNS caching replaces CAM tables for Layer 2 switching.",
                    "DNS caching is used only for backing up router configurations.",
                ],
                "explanation": "Caching improves performance, but stale entries can also complicate troubleshooting.",
                "summary": ["Caching reduces lookup time.", "TTL values affect how long old answers persist."],
                "key_terms": ["DNS cache", "TTL", "resolver", "lookup"],
                "memory_tip": "Fast answers help until they become old answers.",
            }
        ],
        "Network Implementation": [
            {
                "concept": "PoE",
                "correct": "Power over Ethernet delivers electrical power and data over the same Ethernet cabling for supported devices.",
                "distractors": [
                    "PoE is a routing protocol used between branch routers.",
                    "PoE is a storage technology for parity-based RAID sets.",
                    "PoE replaces DHCP by assigning addresses through the cable plant.",
                ],
                "explanation": "PoE simplifies deployment for devices such as phones, cameras, and access points.",
                "summary": ["One cable can carry both power and connectivity.", "Switch capability matters for deployment planning."],
                "key_terms": ["PoE", "Ethernet", "switch", "access point"],
                "memory_tip": "If the endpoint needs watts, check the switch budget.",
            }
        ],
        "Network Operations": [
            {
                "concept": "change management",
                "correct": "Change management reduces operational risk by reviewing, approving, and documenting planned network changes.",
                "distractors": [
                    "Change management is used only for end-user password resets.",
                    "Change management guarantees there will never be outages.",
                    "Change management replaces network diagrams and inventory records.",
                ],
                "explanation": "Most painful outages come from uncontrolled changes, not just hardware faults.",
                "summary": ["Good ops means disciplined change, not cowboy edits.", "Documentation and review reduce avoidable downtime."],
                "key_terms": ["change management", "approval", "documentation", "risk"],
                "memory_tip": "Fast change without control becomes slow recovery.",
            }
        ],
        "Network Security": [
            {
                "concept": "network access control",
                "correct": "Network access control evaluates device or user posture before granting network access.",
                "distractors": [
                    "Network access control is used only for disk encryption policy.",
                    "Network access control replaces every firewall policy in the environment.",
                    "Network access control means every device joins the network without authentication.",
                ],
                "explanation": "NAC helps prevent unmanaged or noncompliant systems from joining trusted network segments.",
                "summary": ["Access should be conditional, not automatic.", "Identity and posture both matter at the edge."],
                "key_terms": ["NAC", "posture", "authentication", "access"],
                "memory_tip": "Do not trust the device just because it plugged in.",
            }
        ],
        "Troubleshooting": [
            {
                "concept": "packet capture",
                "correct": "Packet capture helps troubleshoot by revealing real traffic behavior instead of relying only on assumptions.",
                "distractors": [
                    "Packet capture permanently fixes routing loops by itself.",
                    "Packet capture is used only for assigning VLAN IDs to switchports.",
                    "Packet capture replaces the need for baselines and documentation.",
                ],
                "explanation": "When symptoms are unclear, packet-level evidence can confirm what is actually happening on the wire.",
                "summary": ["Captures provide evidence, not guesses.", "Use them when counters and logs are not enough."],
                "key_terms": ["packet capture", "analysis", "traffic", "evidence"],
                "memory_tip": "When the story is fuzzy, inspect the packets.",
            }
        ],
    },
}
