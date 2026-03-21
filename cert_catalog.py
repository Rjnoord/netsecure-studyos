from __future__ import annotations


CERT_BLUEPRINTS = {
    # CompTIA
    "Tech+": {
        "provider": "CompTIA",
        "domains": ["Core IT Concepts", "Devices & Connectivity", "Apps & Software", "Security Basics"],
    },
    "A+": {
        "provider": "CompTIA",
        "domains": ["Hardware", "Operating Systems", "Networking", "Security", "Troubleshooting"],
    },
    "Network+": {
        "provider": "CompTIA",
        "domains": ["Networking Concepts", "Network Implementation", "Network Operations", "Network Security", "Troubleshooting"],
    },
    "Security+": {
        "provider": "CompTIA",
        "domains": ["General Security Concepts", "Threats & Vulnerabilities", "Security Architecture", "Security Operations", "Governance & Risk"],
    },
    "Linux+": {
        "provider": "CompTIA",
        "domains": ["System Management", "Security", "Scripting & Automation", "Troubleshooting", "Networking & Services"],
    },
    "Cloud+": {
        "provider": "CompTIA",
        "domains": ["Cloud Architecture", "Deployment", "Operations", "Security", "Troubleshooting"],
    },
    "Server+": {
        "provider": "CompTIA",
        "domains": ["Server Hardware", "Administration", "Storage", "Security", "Troubleshooting & DR"],
    },
    "Project+": {
        "provider": "CompTIA",
        "domains": ["Project Concepts", "Planning", "Execution", "Communication", "Risk & Compliance"],
    },
    "Cloud Essentials+": {
        "provider": "CompTIA",
        "domains": ["Cloud Principles", "Business Value", "Governance & Risk", "Management", "Operations"],
    },
    "CySA+": {
        "provider": "CompTIA",
        "domains": ["Security Operations", "Vulnerability Management", "Incident Response", "Threat Intelligence", "Reporting & Communication"],
    },
    "PenTest+": {
        "provider": "CompTIA",
        "domains": ["Planning & Scoping", "Reconnaissance", "Exploitation", "Reporting", "Compliance & Safety"],
    },
    "SecurityX": {
        "provider": "CompTIA",
        "domains": ["Enterprise Security Architecture", "Risk & Governance", "Research & Collaboration", "Integration", "Advanced Operations"],
    },
    "Data+": {
        "provider": "CompTIA",
        "domains": ["Data Concepts", "Data Mining", "Visualization", "Governance", "Analytics"],
    },
    "DataSys+": {
        "provider": "CompTIA",
        "domains": ["Database Design", "Deployment", "Administration", "Security", "Troubleshooting"],
    },
    "DataX": {
        "provider": "CompTIA",
        "domains": ["Data Science Lifecycle", "Model Development", "Evaluation", "Deployment", "Governance"],
    },
    "CloudNetX": {
        "provider": "CompTIA",
        "domains": ["Cloud Networking", "Architecture", "Security", "Operations", "Optimization"],
    },
    # AWS
    "AWS Cloud Practitioner": {
        "provider": "AWS",
        "domains": ["Cloud Concepts", "Security & Compliance", "Technology", "Billing & Pricing"],
    },
    "AWS AI Practitioner": {
        "provider": "AWS",
        "domains": ["AI/ML Concepts", "Generative AI", "Responsible AI", "AWS AI Services"],
    },
    "AWS Solutions Architect Associate": {
        "provider": "AWS",
        "domains": ["Secure Architectures", "Resilient Architectures", "High-Performance Architectures", "Cost-Optimized Architectures"],
    },
    "AWS Developer Associate": {
        "provider": "AWS",
        "domains": ["Development with AWS Services", "Security", "Deployment", "Troubleshooting & Optimization"],
    },
    "AWS CloudOps Engineer Associate": {
        "provider": "AWS",
        "domains": ["Monitoring & Operations", "Reliability", "Security & Compliance", "Networking & Content Delivery", "Cost & Performance"],
    },
    "AWS Data Engineer Associate": {
        "provider": "AWS",
        "domains": ["Data Ingestion", "Storage", "Transformation", "Orchestration", "Security & Governance"],
    },
    "AWS Machine Learning Engineer Associate": {
        "provider": "AWS",
        "domains": ["ML Data Preparation", "Model Development", "Deployment", "Operations", "Monitoring"],
    },
    "AWS Solutions Architect Professional": {
        "provider": "AWS",
        "domains": ["Complex Architecture Design", "Migration", "Cost Control", "Governance", "Hybrid Strategy"],
    },
    "AWS DevOps Engineer Professional": {
        "provider": "AWS",
        "domains": ["SDLC Automation", "Configuration Management", "Observability", "Incident Response", "Security & Compliance"],
    },
    "AWS Generative AI Developer Professional": {
        "provider": "AWS",
        "domains": ["Foundation Models", "Prompt Engineering", "Application Integration", "Security & Governance", "Evaluation & Operations"],
    },
    "AWS Advanced Networking Specialty": {
        "provider": "AWS",
        "domains": ["Network Design", "Hybrid Connectivity", "Network Security", "Automation", "Troubleshooting"],
    },
    "AWS Security Specialty": {
        "provider": "AWS",
        "domains": ["Identity & Access", "Detection", "Infrastructure Security", "Data Protection", "Incident Response"],
    },
    "AWS Machine Learning Specialty": {
        "provider": "AWS",
        "domains": ["ML Engineering", "Modeling", "Deployment", "Operations", "Governance"],
    },
    # Azure
    "AZ-900": {
        "provider": "Azure",
        "domains": ["Cloud Concepts", "Core Azure Services", "Azure Management & Governance", "Identity & Security"],
    },
    "AI-900": {
        "provider": "Azure",
        "domains": ["AI Workloads", "Machine Learning", "Computer Vision", "NLP & Generative AI"],
    },
    "DP-900": {
        "provider": "Azure",
        "domains": ["Core Data Concepts", "Relational Data", "Non-Relational Data", "Analytics"],
    },
    "SC-900": {
        "provider": "Azure",
        "domains": ["Identity Concepts", "Security Concepts", "Compliance", "Microsoft Security Solutions"],
    },
    "AZ-104": {
        "provider": "Azure",
        "domains": ["Identity", "Storage", "Compute", "Networking", "Monitoring & Governance"],
    },
    "AZ-204": {
        "provider": "Azure",
        "domains": ["App Services", "Functions & Containers", "Storage", "Security", "Monitoring"],
    },
    "AZ-305": {
        "provider": "Azure",
        "domains": ["Architecture Design", "Identity & Security", "Data Storage", "Business Continuity", "Governance"],
    },
    "AZ-400": {
        "provider": "Azure",
        "domains": ["Source Control", "CI/CD", "Infrastructure as Code", "Observability", "Security & Compliance"],
    },
    "AZ-500": {
        "provider": "Azure",
        "domains": ["Identity Security", "Platform Protection", "Security Operations", "Data & Application Security"],
    },
    "AZ-700": {
        "provider": "Azure",
        "domains": ["Network Design", "Hybrid Connectivity", "Private Access", "Load Balancing", "Monitoring"],
    },
    "AZ-800": {
        "provider": "Azure",
        "domains": ["Hybrid Identity", "Windows Server Administration", "Active Directory", "File & Storage", "Networking", "Security", "Monitoring & Recovery"],
    },
    "Windows Server Hybrid Administrator Associate": {
        "provider": "Azure",
        "domains": ["Hybrid Server Deployment", "Identity", "Administration", "Networking", "Recovery"],
    },
    "Azure AI Engineer Associate": {
        "provider": "Azure",
        "domains": ["Plan AI Solutions", "Computer Vision", "NLP", "Knowledge Mining", "Generative AI"],
    },
    "Azure Data Engineer Associate": {
        "provider": "Azure",
        "domains": ["Data Storage", "Data Processing", "Security", "Monitoring", "Optimization"],
    },
    "Azure Database Administrator Associate": {
        "provider": "Azure",
        "domains": ["Deployment", "Configuration", "Security", "Monitoring", "Optimization"],
    },
    "Azure Data Scientist Associate": {
        "provider": "Azure",
        "domains": ["Data Prep", "Model Training", "Experimentation", "Deployment", "Monitoring"],
    },
    "Azure Virtual Desktop Specialty": {
        "provider": "Azure",
        "domains": ["Identity & Access", "Host Pools", "Images & Apps", "Monitoring", "Security"],
    },
    "Azure Network Engineer Associate": {
        "provider": "Azure",
        "domains": ["Hybrid Networking", "Private Access", "Traffic Distribution", "Security", "Observability"],
    },
    "Azure Security Engineer Associate": {
        "provider": "Azure",
        "domains": ["Identity Protection", "Platform Security", "Defender for Cloud", "Data Security", "Incident Response"],
    },
    # Cisco
    "CCST Networking": {
        "provider": "Cisco",
        "domains": ["Network Basics", "Connectivity", "IP Services", "Security Basics", "Troubleshooting"],
    },
    "CCST Cybersecurity": {
        "provider": "Cisco",
        "domains": ["Threats", "Access Control", "Security Monitoring", "Networking Basics", "Incident Response"],
    },
    "CCST IT Support": {
        "provider": "Cisco",
        "domains": ["Devices", "OS Support", "Networking", "Security", "Troubleshooting"],
    },
    "CCT Field Technician": {
        "provider": "Cisco",
        "domains": ["Hardware", "Diagnostics", "Replacement Procedures", "Safety", "Documentation"],
    },
    "CCNA": {
        "provider": "Cisco",
        "domains": ["Network Fundamentals", "Network Access", "IP Connectivity", "IP Services", "Security Fundamentals", "Automation & Programmability"],
    },
    "CCNA Automation": {
        "provider": "Cisco",
        "domains": ["Programming Basics", "APIs", "Automation Workflows", "Data Formats", "Security", "Operations"],
    },
    "CyberOps Associate": {
        "provider": "Cisco",
        "domains": ["Security Concepts", "Monitoring", "Host-Based Analysis", "Network Intrusion Analysis", "Incident Response"],
    },
    "CCNP Enterprise": {
        "provider": "Cisco",
        "domains": ["Enterprise Core", "Advanced Routing", "SD-WAN", "Wireless", "Automation"],
    },
    "CCNP Security": {
        "provider": "Cisco",
        "domains": ["Secure Access", "Firewalling", "Email/Web Security", "VPN", "Automation"],
    },
    "CCNP Data Center": {
        "provider": "Cisco",
        "domains": ["Data Center Core", "Networking", "Compute", "Storage", "Automation"],
    },
    "CCNP Collaboration": {
        "provider": "Cisco",
        "domains": ["Call Control", "Endpoints", "QoS", "Collaboration Apps", "Automation"],
    },
    "CCNP Service Provider": {
        "provider": "Cisco",
        "domains": ["SP Core", "Routing", "Services", "Automation", "Assurance"],
    },
    "CCNP Automation": {
        "provider": "Cisco",
        "domains": ["Software Design", "APIs", "Automation Pipelines", "Security", "Observability"],
    },
    "CCIE Enterprise Infrastructure": {
        "provider": "Cisco",
        "domains": ["Advanced Routing", "Enterprise Design", "Segmentation", "Services", "Automation"],
    },
    "CCIE Enterprise Wireless": {
        "provider": "Cisco",
        "domains": ["Wireless Design", "RF Concepts", "Security", "Operations", "Troubleshooting"],
    },
    "CCIE Security": {
        "provider": "Cisco",
        "domains": ["Zero Trust", "Perimeter Security", "Identity", "Detection & Response", "Automation"],
    },
    "CCIE Data Center": {
        "provider": "Cisco",
        "domains": ["Fabric Design", "Compute", "Storage", "Virtualization", "Automation"],
    },
    "CCIE Collaboration": {
        "provider": "Cisco",
        "domains": ["Voice", "Video", "QoS", "UC Applications", "Automation"],
    },
    "CCIE Service Provider": {
        "provider": "Cisco",
        "domains": ["Carrier Routing", "MPLS", "Services", "Automation", "Operations"],
    },
    "CCIE Automation": {
        "provider": "Cisco",
        "domains": ["Application Design", "APIs", "Automation Pipelines", "Security", "Observability"],
    },
    "CCDE": {
        "provider": "Cisco",
        "domains": ["Network Design", "Business Requirements", "Architecture Tradeoffs", "Scalability", "Operations"],
    },
}


def catalog_domains() -> dict[str, list[str]]:
    return {exam: blueprint["domains"] for exam, blueprint in CERT_BLUEPRINTS.items()}


def catalog_provider(exam: str) -> str:
    return CERT_BLUEPRINTS[exam]["provider"]
