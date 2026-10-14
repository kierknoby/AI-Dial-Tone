# Project Overview

The project is developing an open-source communications platform that enables autonomous AI agents to make telephone calls over the existing global telephone network.

As artificial intelligence becomes increasingly capable of completing tasks independently, access to traditional telecommunications remains a significant limitation. AI agents can interact with websites, software, and digital services, but making an ordinary telephone call still requires specialist integrations, infrastructure, and human intervention.

The objective is to change that.

An autonomous agent should be able to discover a telephone service, obtain authorisation from its human, pay for calling access where required, establish a connection, conduct a natural conversation, and report the outcome. Whether booking a restaurant, contacting a supplier, arranging an appointment, or communicating with another automated system, the underlying telecommunications should be largely invisible to the agent.

For managed calling, x402 enables autonomous agents to pay for telephone access programmatically, without conventional subscriptions, manual checkout processes, or pre-existing commercial relationships.

The communications architecture is built around established SIP and PJSIP standards, with Asterisk and FreePBX providing the reference telephony environment. It draws on existing softphone engineering principles to incorporate registration, pre-call readiness qualification, secure signalling and media, real-time diagnostics, and reliable call control into an interface designed specifically for autonomous software.

Human authorisation remains central. Calls must operate within defined permissions, destinations, durations, and spending limits, with safeguards that operate independently of the AI agent itself.

The platform is designed to support both self-hosted telecommunications infrastructure and managed calling services through a common agent-facing interface. Developers can bring their own compatible telephone systems, while others can obtain calling access without operating a PBX.

Its open-source approach encourages interoperability, independent development, and adoption across different AI models, agent frameworks, and telecommunications providers.

The initial implementation includes local agent-to-agent audio communication, experimental speech processing, simulated Asterisk connectivity, and x402 payment-admission components. Production telephone calling, live payment settlement, and reliable unscripted conversations remain under development.

The goal is not to build another AI assistant or another softphone. It is to give autonomous AI agents access to the telephone network as a standard, secure, and programmable capability.
