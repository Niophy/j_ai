# J_AI Evaluation Report

Course: ITE 402 | Provider: OllamaProvider:qwen3.8:27b:think=low | Generated: 2026-10-12 10:18

## Scoreboard

| Metric | Value |
|---|---|
| cases total | 5 |
| cases graded | 5 |
| cases guard rejected | 0 |
| cases provider error | 0 |
| cases bad score value | 0 |
| average score | 6.0 |
| pass rate | 0.6 |
| avg model latency seconds | 71.61 |
| average: requirements_analysis | 5.5 |
| average: logical_design | 8.0 |
| average: protocol_selection | 9.0 |
| average: security_strategy | 2.0 |

## REQ_001 | requirements_analysis | 9/10 PASS (graded)

**Question:** A small clinic has 1 main site and 1 remote branch. They need reliable internet access, secure patient record access, and minimal downtime. Budget is limited. They expect growth from 30 to 80 staff within 2 years.

**Answer:**

> A clinic with 1 main site and 1 remote branch, 30 staff growing to 80 in 2 years, limited budget, so I'll separate the goals first. Business goals: keep patient care running with minimal downtime, let both sites share patient records so a patient can visit either one, and grow to 80 staff without rebuilding everything. Technical goals: reliable internet at both sites (a main ISP plus a cheaper backup link so one failure doesn't stop the clinic), a site-to-site VPN between main and branch, and a network that keeps clinical traffic and admin/guest traffic apart. Constraints: the budget is limited so I'd pick affordable business-grade equipment over enterprise, the IT staff is probably small or outsourced so it has to be simple to manage, and the branch only works normal weekday hours. Growth: size the switches and the IP plan for 80 users from day one (spare ports and room in the subnets) so going from 30 to 80 is adding devices not redesigning. Security: patient records need encryption in transit (the VPN) and at rest, a firewall at each site, user accounts with MFA, and access by role so reception doesn't see what doctors see. I won't assume a specific vendor or price since the scenario doesn't give them.

**Strengths:**
- Clearly and explicitly separated business goals from technical goals with distinct labels
- Identified multiple constraints including budget, staffing, and branch operating hours
- Scalability addressed with a concrete strategy: size switches and IP plan for 80 users from day one
- Security covered comprehensively: encryption in transit and at rest, firewalls, MFA, and role-based access control
- Avoided inventing vendor names or prices, staying faithful to the scenario's information

## REQ_002 | requirements_analysis | 2/10 FAIL (graded)

**Question:** A university building has 6 labs and 12 classrooms. Each lab has 35 PCs. WiFi must cover classrooms. Some devices are IoT sensors. The network must support online exams without drops. IT staff is small.

**Answer:**

> A university building with 6 labs, 35 PCs each, 12 classrooms, WiFi, some IoT sensors, online exams must not drop and a small IT staff. So the main thing is availability, the exams can't drop, so we need backup, a second internet link and backup power (UPS) for the lab rooms so if something fails the exam keeps going. WiFi has to cover all 12 classrooms so we put access points in each classroom, maybe 1 or 2 depending on the size of the room, and the students and staff connect to it. The 6 labs need 210 PCs in total so we need enough switches for all of them, 35 each. The IoT sensors could connect to the WiFi too.

**Missing Points:**
- traffic types
- management
- segmentation

**Strengths:**
- Correctly identified availability as the primary design driver for exam continuity
- Proposed a second internet link for redundancy
- Proposed UPS backup power for lab rooms
- Addressed wireless coverage by placing access points in each classroom

## LOG_001 | logical_design | 8/10 PASS (graded)

**Question:** A mid size company has 3 departments: HR, Finance, Engineering. Engineering has heavy internal traffic and needs lab isolation. Finance needs strict access control. Provide a logical design approach.

**Answer:**

> A mid size company with HR, Finance and Engineering, Engineering has heavy internal traffic and needs lab isolation, Finance needs strict access. So I'd use a hierarchical design with 3 layers: access layer switches where the users plug in, a distribution layer that routes between departments and applies the policies, and a core layer that is just fast switching. Segmentation: each department gets its own VLAN (HR, Finance, Engineering) and the Engineering lab gets a separate VLAN so its traffic stays isolated from production, plus a management VLAN for the devices. Addressing plan: a subnet per VLAN from 10.x.x.x private range, for example HR 10.10.10.0/24, Finance 10.20.20.0/24, Engineering a bigger /23 because it has more devices and traffic, Lab 10.40.40.0/24, management 10.99.0.0/24. Routing approach: inter-VLAN routing at the distribution layer on layer 3 switches, with ACLs so Finance only accepts the traffic it needs (strict access) and the lab can't reach the other departments, and OSPF between the distribution and core if the company grows to more sites. Redundancy: two distribution switches with HSRP/VRRP for the default gateway, dual uplinks from the access switches, and link aggregation on the core links so one failure doesn't take a department down.

**Design Flaws:**
- OSPF is mentioned only as a future consideration ('if the company grows to more sites'), which is reasonable but leaves the single-site routing model slightly under-specified — no mention of whether static routes or a default route would be used at the core for a single-site deployment.
- The strict access control for Finance is addressed via ACLs on L3 switches, but no mention of a dedicated firewall or security appliance between Finance and other VLANs, which would be more robust for 'strict access control' in a mid-size company.

**Strengths:**
- Clear three-tier hierarchy (access, distribution, core) with distinct roles for each layer.
- Segmentation is well-justified: separate VLANs per department, a dedicated lab VLAN for isolation, and a management VLAN — all tied back to the scenario requirements.
- Addressing plan is structured, uses private ranges, and the /23 for Engineering is explicitly justified by higher device count and traffic.
- Routing approach is logical: inter-VLAN routing at distribution with ACLs enforcing the Finance and lab isolation requirements.
- Redundancy is multi-layered: HSRP/VRRP for gateway, dual uplinks from access, and link aggregation on core links.

## PROT_001 | protocol_selection | 9/10 PASS (graded)

**Question:** Choose a routing protocol for a campus network with multiple buildings and future growth. Justify your choice briefly.

**Answer:**

> A campus with multiple buildings and future growth, so I'd choose OSPF. OSPF is a link state protocol, so every router has a full map of the network and calculates the best path itself, which means it converges fast when a link goes down compared to distance vector protocols like RIP. It's scalable because you can split the campus into areas (area 0 as the backbone and an area per building or group of buildings), so routing updates stay inside an area and adding a new building later is just adding a new area. It's also an open standard so it works with any vendor, which matters if the campus buys different equipment over the years.

**Strengths:**
- Correctly identifies OSPF and explains it as a link state protocol
- Addresses scalability through multi-area design (area 0 backbone + per-building areas)
- Mentions fast convergence compared to distance vector protocols like RIP
- Notes vendor independence as an open standard, relevant for mixed-equipment campuses
- Explains that adding a new building is simply adding a new area, directly addressing future growth

## SEC_001 | security_strategy | 2/10 FAIL (graded)

**Question:** A company allows remote work. They host internal apps and a public website. Propose security strategies for internal and perimeter security.

**Answer:**

> A company with remote work, internal apps and a public website. So for the perimeter I'd put a firewall between the internet and the company network to block what shouldn't come in, and the remote workers connect through a VPN so their connection is encrypted when they reach the internal apps from home. The website should also have HTTPS. Staff should use strong passwords and get training so they don't click phishing emails.

**Missing Controls:**
- segmentation
- least privilege
- monitoring
- public facing isolation

**Risk Gaps:**
- No network segmentation between internal apps and the public website is described; a single firewall is mentioned but no internal zone separation
- No least privilege or access control model is referenced for internal app access
- No monitoring, logging, or alerting is mentioned for detecting intrusions or anomalies
- The public website is not isolated from internal infrastructure (e.g., DMZ, separate hosting, WAF)

**Strengths:**
- Remote access is protected via VPN with encryption
- HTTPS is specified for the public website
- Phishing awareness training is mentioned as a human-layer control

