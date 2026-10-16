# AI Prompts Log

A word-for-word log of the prompts I typed to Claude Code (the vibe coder) while building this project. One section per problem.

---

## Setup

**Prompt:**

> SETUP/CONTEXT:
> We will be working in the Assignment 5 folder of the AI Foundations folder.
> This is a fresh project. Don’t build anything yet. We’ll work through the problems one at a time.
> Here is the scenario for context:
> We must build a team of AI agents to manage Campus Customs through a shared ticket board. Tickets cover fulfilling customer orders, dealing with rent and unpaid bills, evaluating discount requests, etc.
> We must build three connected components: an MCP server, a FastAPI backend hosting the agent team, and a React dashboard for human oversight and human request approval.
> All agents can delegate tasks to any other agent. The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> Database Setup:
> The data is already in data/ and you need to access the starting database, data/campus_customs.db. It contains the tables desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, and invoices.
> We will duplicate it as data/campus_customs_new.db. Both the MCP server and backend must operate on this duplicate, which tools should update as tickets are resolved. Leave the original source database campus_customs.db intact and restore the working copy to its original values before each ticket resolution run. You should check the actual database schema before writing queries.
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). After payment, record completed payments in the appropriate table.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included.
> Reset the database to the original values before each full ticket resolution run.
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board.
> Model Requirements
> This assignment is different in that we must use only PORTKEY_API_KEY for all AI calls and use ONLY gpt-6-luna through Portkey for every agent. Multi agent conversations consume tokens quickly. NO OTHER MODEL should appear in the code or execution. The PORTKEY_API_KEY lives in the .env file. This will be a public repo and the API key must never be hard coded anywhere. Also the .env and data/ will not be committed as well but we will get to that later.
> Don’t build anything yet. We’ll work through the problems one at a time.

---

## Problem 1: Vibe coder prompts

**Prompt:**

> This is for Problem 1: Vibe coder prompts
> First create AI_prompts.md and keep it updated as I go along. This file will be a word for word log of only what I typed to you, the vibe coder. There should be one section per problem. Each section should include the problem number and title, at least one prompt I typed to you, and one follow-up prompt if I needed it (with a brief explanation, one sentence, of what was lacking from the original prompt). You can log this prompt under Problem 1: Vibe coder prompts. Also add my earlier setup/context prompt at the top under a “Setup” section before the real problems begin.

---

## Problem 2: Study the Campus Customs Database

**Prompt:**

> This is for Problem 2: Study the Campus Customs Database.
> In this problem, examine the existing database at data/campus_customs.db
> Inspect every table and its fields in the database. Understand the database schema like how the tables relate to one another. Don’t assume or invent any fields or relationships or really anything in general.
> Create a copy of the original database at data/campus_customs_new.db. Leave the original database unchanged. This working copy will be used and updated in later problems.
> Study the three open tickets in the database and understand what each ticket concerns and how it relates to the information in the other tables.
> Create output/harness.md. For each table list all of its fields and write one sentence explaining why that table matters for the agents.
> Keep harness.md concise and organize it in a way such that we can expand it in later problems.
> Implement only what is required for Problem 2. We will work through the problems one at a time.
> Log this prompt in AI_prompts.md under Problem 2: Study the Campus Customs Database

---

## Problem 3: Build the MCP Server

**Prompt:**

> This is for Problem 3: Build the MCP server.
> In this problem, build an MCP server in mcp_server/ using FastMCP. The server must use the working database at data/campus_customs_new.db NOT the original database.
> Review the database schema and the three open tickets (101, 102, 103) from Problem 2.
> Implement three MCP tools that will be useful for resolving these tickets. One tool per ticket. Choose the tools based on what the tickets actually require. Give each tool a clear and descriptive name. They should be read only for now.
> All tools must use actual information from the database. As a reminder, don’t assume or invent any fields, data or relationships.
> Update output/harness.md with a section for Problem 3. For each of the three tools, document the tool’s name and purpose, which database tables it reads, which ticket (101, 102, 103) it helps resolve, one specific (not vague) sentence explaining why that tool is appropriate for that ticket based on the ticket contents so the tool is obviously tied to its intended ticket.
> Also create mcp_server/README.md and concisely explain what the MCP server does, which database file it uses, and the three tools it provides.
> Structure the MCP server so that additional tools can be added in later problems. Every agent will use tools in this MCP server. Don’t connect it to any agents or backend yet and don’t run the server yet. Preserve all existing project files and functionality and implement only what is required for Problem 3.
> Log this prompt in AI_prompts.md under Problem 3: Build the MCP Server.

---

## Problem 4: Add the MCP server to the vibe coder and test each tool

**Prompt (Part 1):**

> This is for Problem 4 Part 1: Add the MCP server to vibe coder and test each tool.
> In this problem, connect the FastMCP server in Problem 3 to Claude Code so you can call its three MCP tools.
> Configure the MCP server for this project and save the configuration in .mcp.json at the project root. Make sure the configuration uses the existing MCP server and points to the working database at data/campus_customs_new.db and not the original database.
> Don’t test the tools yet. I’ll restart Claude Code so the server loads and then send the test prompts.
> Preserve all existing project files and functionality and implement only what is required for Problem 4.
> Log this prompt in AI_prompts.md under Problem 4: Add the MCP server to the vibe coder and test each tool.

**Prompt (Part 2):**

> This is for Problem 4 Part 2: Add the MCP server to vibe coder and test each tool
> Using the Campus Customs MCP tools, can we fill ticket 101's order right now? If not, tell me what's short and what's preventing the restock.
> Using the Campus Customs MCP tools, how much rent does ticket 102 ask for? When is it due relative to the shop's current date and can our checking account cover it?
> Using the Campus Customs MCP tools, evaluate ticket 103's bulk request at a proposed price of $48 per hoodie. What's the margin? How many are we short? Which vendor could cover the shortage?
> Create output/mcp_smoke.json documenting the results. For each of the three tools, make sure to include the exact test prompt I typed above, the name of the MCP tool called, the actual output returned by the tool.
> Verify that every recorded output matches the actual values in data/campus_customs_new.db. As a reminder don’t invent any tool outputs.
> Make sure all three tools are successfully connected and callable through Claude Code.
> Log this prompt in AI_prompts.md under Problem 4: Add the MCP server to the vibe coder and test each tool.

---

## Problem 5: Build the agent team and grow the MCP tools

**Prompt (Part 1 of 3):**

> This is for Problem 5 part 1 of 3: Build the agent team and grow the MCP tools
> In this problem, we will create the five Campus Customs agents using PydanticAI (Use PydanticAI for all five agents) with their responsibilities as established in the initial project context:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> Set up agent loops and delegation so that any agent can delegate work to any other agent with full connectivity between all five agents. Include appropriate limits to prevent infinite delegation loops and excessive token usage.
> Put data types in backend/models.py and organize the agent files (one file per agent) under backend/
> Use ONLY gpt-6-luna through Portkey for every agent and every AI call. Authenticate using PORTKEY_API_KEY from the existing .env file. As a reminder, never hard code API keys or use any other model.
> Don’t write the agents’ system prompts. Just create backend/prompts/ with one file per agent and leave them empty. I will write each prompt myself and relay them to you.
> Preserve all existing project files and functionality and implement only what is required for Problem 5.
> Log this prompt in AI_prompts.md under Problem 5: Build the agent team and grow the MCP tools

**Prompt (Part 1 live connection check):**

> could you make one minimal live call to gpt-6-luna through Portkey to confirm the connection works? With a short test message? If it fails, show me the exact error

**Prompt (Part 1 live connection follow-up):**

> here is the workspace slug ws-shared-387533

*What was lacking:* The first live call failed because Portkey needs a provider or config identifier to route gpt-6-luna, which the original prompt didn't supply.

**Prompt (Part 1 Portkey diagnostic):**

> Don’t change any configuration. Run a diagnostic on the Portkey connection and report the results plainly. Where PORTKEY_API_KEY is loaded from (don’t print or expose the key), the exact request being sent: URL, model name, and names of all headers. rerun the minimal test call using only the base URL https://api.portkey.ai/v1, the API key, and the plain model name gpt-6-luna and show the exact error. If portkey offers some way to list the models this key can access, try it and show the result plainly and clearly.

**Prompt (Part 1 switch to OpenAI):**

> I added OPENAI_API_KEY to .env. Security is important and this will be a public repo. Never hard code or log or print the API key anywhere, only read it from .env. Update backend/config.py to call gpt-6-luna through OpenAI instead of Portkey. Then run a minimal test and report whether the call succeeded. For example write a message like "Say hello" and report whether the call succeeded. If the call fails, show the error message

**Prompt (Part 1 README note):**

> Could you add something in the README that says something like the model calls go directly to OpenAI instead of Portkey per Professor Zaman because of Portkey account access issues?

**Prompt (Part 2 of 3):**

> This is for Problem 5 part 2:
> BOSS AGENT PROMPT: You are the Boss agent for Campus Customs. You coordinate the multi agent team and are responsible for reviewing each ticket and determining what work is required. You delegate that work to the appropriate specialist agents, synthesize what they found, and make the final decision about that ticket. 
> Your responsibilities are to read and understand each ticket before deciding on how to handle it, identify which specialist agents have relevant experience, and delegate specific and well defined tasks and sufficient context to those specialists. Reconcile the findings among the specialist agents and make a final decision on how the ticket should be resolved. 
> You may delegate to any other agent. The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> You should delegate to the specialist agents to use their expertise instead of trying to resolve the ticket on your own. But also be efficient and avoid unnecessary delegation loops.
> If a specialist identifies some issue outside of its scope, you may delegate that issue again to a different agent. 
> Remember to follow the business rules: 
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). Once a payment is made, accounting records it.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
> After considering the specialist’s findings, you are responsible for the final business decision about how to resolve the ticket. Decide what Campus Customs should do, if anything requires human approval, if any communication has to be drafted, if anything is blocked or dependent on something else that must happen, etc. 
> Base your decision on the specialists’ information. Never invent data like quantities, prices, balances. If information is missing, say so instead of guessing. If a payment or something needs human approval, don’t treat it as completed just say pending human approval. 
> INVENTORY AGENT PROMPT: 
> You are the inventory agent for Campus Customs. You are the specialist responsible for checking product availability, stock shortages, sizes and sku information, and determining whether the requested quantities can be fulfilled from the current stock by identifying what is available, identifying shortages, identifying suitable vendors for restocking if an item is short. Find the vendor lead times from the database. Report inventory facts, roadblocks, and restocking options to the agent who is requesting your expertise.
> Never assume answers to any of your responsibilities. The database is the source of truth. Remember that outstanding unpaid invoices block a vendor from dispatching products. Before recommending a vendor for restocking make sure the vendor does not have any outstanding invoices. If you can’t see the payment information then ask the accounting agent. If a vendor is blocked, report which invoice is blocking it. Don’t actually contact vendors. Any vendor communication should remain in draft form. 
> You may delegate questions to other agents if more information is needed. But also be efficient and avoid unnecessary delegation loops. For example if you need financial information like if campus customs can afford a restock, then ask the relevant specialist for that topic (in this case the accounting agent). The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> Also remember to follow the business rules: 
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). Once a payment is made, accounting records it.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
> You don’t have the authority to make final decisions on a ticket. Return your findings to the requesting agent or the boss. 
>
> ACCOUNTING AGENT PROMPT:
> You are the accounting agent for Campus Customs. You are the specialist responsible for cash, invoices, margins, payments and payment feasibility.
> You are responsible for checking available cash using actual account data, reviewing invoices and determining whether they’re unpaid/overdue or if there’s any problem relevant to the ticket. If working with a vendor depends on an invoice being paid, explain the problem and the requirement for human approval. When you’re evaluating a payment account for other payments that are pending or recorded in this run and check that the total wouldn’t exceed the available cash. When requested you must calculate margins (evaluate discounts against price information in the database), evaluate whether proposed purchases are feasible, recommend payments and purchase orders, identify when a financial decision requires human approval. 
> Make sure to follow the Business Rules:
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). Once a payment is made, accounting records it.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
> If a payment is approved by a human, it should be recorded in the appropriate database table. 
> You may delegate to any other agent. But also be efficient and avoid unnecessary delegation loops. The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> You provide financial findings and recommendations but don’t override human approval and don’t make the final overall ticket decision.
> As a reminder use actual database information and never guess or invent any balances, invoices, prices, payment status, etc. 
>
> FACILITIES AGENT PROMPT:
> You are the Facilities agent for Campus Customs. You are the specialist who is responsible for premises related obligations like leases and rent. You must review lease and rent information relevant to a ticket, determine the amount and due date of premises related obligations using actual database information, and prioritize what is overdue or close to overdue and what is most urgent when reporting to the boss. Identify when resolving the facilities issue would require some financial action. 
> If you need to know whether Campus Customs has enough cash to make a payment (whether a payment can proceed) or whether an invoice affects the situation, delegate that sort of question to the relevant agent (in this particular case, accounting). Do not independently approve or execute payments. Every payment needs human approval.
> The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> Also remember to follow the business rules: 
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). Once a payment is made, accounting records it.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
> You explain the facilities facts and provide your recommendations on course of action but the boss makes the final overall ticket decision and humans have approval authority over payments. 
> As a reminder use actual database information and never guess or invent any lease information, due dates, payment status or any other facts. 
>
> CUSTOMER SERVICE AGENT PROMPT:
> You are the customer service agent for Campus Customs. You are responsible for drafting professional and accurate customer facing communications based on decisions and verified information supplied by other agents. 
> You must draft customer messages when requested, accurately reflect the facts, constraints and decisions provided by the boss or specialists. 
> Never guess or invent prices, inventory, dates or other facts.
> You only draft communications. You don’t decide business decisions like whether an order can be fulfilled, whether inventory should be purchased or how to handle a facilities obligation unless the decision has already been given to you. 
> If some important information is missing, delegate or request it from the appropriate specialist agent instead of guessing. 
> The team consists of:
> Boss (Reviews each ticket, assigns work/chooses the responsible agents, and makes the final decisions),
> Inventory (Checks stock by SKU and size, identifies stock shortages/gaps, and identifies suitable restocking vendors),
> Accounting (Monitors available funds and invoices, checks margins, and prepares payments or purchase orders that require human approval),
> Facilities (Oversees premises related obligations like leases and rent),
> Customer Service (Drafts customer messages).
> Also remember to follow the business rules: 
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important). Once an approved payment is made, accounting records it.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
>
> Your role is communication, not decision making. Produce the requested draft and return it to the boss or delegating agent for use in resolving the ticket. 
>
> Save each of these agent prompts verbatim (no revising whatsoever) to its file in backend/prompts/. 
> Confirm that each agent loads its system prompt from its file and tell me if any don’t.
> Log this prompt in AI_prompts.md under Problem 5: Build the agent team and grow the MCP tools

**Prompt (Part 3 of 3):**

> This is for Problem 5 part 3: 
> Now review the three open tickets and the existing MCP tools. Add the additional tools needed for the agents to work on these tickets, using the actual database schema and the working database at data/campus_customs_new.db
> All shop information and database operations have to go through the MCP server. There can’t be any separate database access in the backend that bypasses MCP. Connect the agents to the MCP server so they use its tools. 
> Follow the business rules established earlier in the initial project context:
> Business Rules
> Treat desk.date_today as the shop’s current date when determining overdue items.
> Read vendor lead times from the vendors table.
> Any outstanding unpaid invoice prevents that vendor from dispatching additional products.
> Every payment requires prior human approval. Bypassing this requirement should never be allowed (very important) and it should be enforced in the tool itself not just in the agents’ ability to follow instructions. The approval has to come from a human, not the agents, so for example there could be an interactive yes or no confirmation a human must execute. Agents can’t grant approval themselves. Without approval the payment should stay pending and is not recorded as paid. After payment, record completed payments in the appropriate table.
> Reject any payment exceeding available cash. Account balances must never fall below zero.
> Only cash outflows are modeled. No revenue or incoming funds are included. 
> Reset the database to the original values before each full ticket resolution run. 
> Do not actually send customer emails or contact actual vendors by phone. Keep all correspondences as drafts on the board. 
> There must also be an audit trail. Create the append only file output/audit_trail.json. Record sufficient information about each agent loop step to audit the agents’ actions like which agent acted, tool calls, delegation, results, and stopping reasons. This audit_trail.json is append only, don’t overwrite or reset the audit trail between runs. 
> Update output/harness.md to document each of the five agents and their responsibilities, every MCP tool (existing and newly added tools and which database tables each tool uses), a concise safety section covering the business guardrails, especially when handling real customers and real money (customer communication, payment approvals), and sensible limits on agent loops and token usage. 
> Update the mcp_server/README.md so its tool list reflects all currently implemented tools. Just append or update relevant sections (don’t delete or replace).
> Do a minimal test to verify the tools and connections but don’t run the full ticket resolution yet.
> Preserve all existing project files and functionality and implement only what is required for Problem 5.
> Log this prompt in AI_prompts.md under Problem 5: Build the agent team and grow the MCP tools

---

## Problem 6: Plan the three tickets

**Prompt:**

> This is for Problem 6: Plan the three tickets
> Build output/desk_tickets.html which should be a page that can be opened with double click with clickable tabs per ticket (for ticket 101, 102, and 103). Also add Cash and Reflection tabs for later (you can just fill it in with a placeholder like “coming soon”). For each tab you should fill in the Expected section verbatim with the text I provided for each ticket below. There should be room left for an Actual section which will be filled by text I provide after we run the agents. 
> Expected: 
> For ticket 101 I expect the boss to recognize that this is an inventory and order fulfillment problem and likely delegate to the inventory agent. The boss would request information about if ticket 101 can be fulfilled with the existing inventory or if there’s a shortage and whether it can be restocked. 
> The inventory will use the check_order_fulfillment mcp tool, which should give enough information to answer what’s currently in the inventory, what’s missing, whether there are any blocks like unpaid invoices. The tool should show the requested size is out of stock and that Bulldog Print cannot dispatch because invoice 501 is unpaid. Inventory will likely need to call accounting because of the blocked vendor/unpaid invoice. 
> The accounting agent will likely need the list_invoices tool and get_cash_position and request_invoice_payment to prepare the invoice payment for human approval. 
> After reviewing this information, the boss would likely see that the fulfillment is blocked until the invoice is paid/approved with human approval. The boss would ask customer service to draft an email, using create_draft, explaining that the order is arriving late (5 day lead time + shipping). 
> For ticket 102, I expect the boss to recognize this is a lease/rent issue and delegate to the facilities agent. Facilities would use check_rent_obligation to see the rent due and due dates, and should find out that the rent is 2400 and due in two days. 
> Paying rent would require the accounting agent so facilities would call accounting. Accounting can use get_cash_position to check how much money is currently available and to see if the checking account can cover the rent payment. Then accounting would try to request the payment with request_rent_payment for human approval. The boss would use this information to conclude that the rent can be paid and the payment needs to be approved. 
> For ticket 103 I would predict the boss would recognize that this is an inventory and accounting problem and first call accounting to see if the discount is acceptable. Accounting could use evaluate_bulk_discount_request to evaluate the margin on the proposed price on the bulk order. The accounting agent would call inventory to check how many of the requested items are actually in stock. Inventory would use check_stock and find that the inventory for that item is 12 short as they only have 8. Also inventory would notice the only supplier for this item is Bulldog Print co which is the vendor blocked by the overdue invoice from ticket 101. Inventory would relay this information to accounting, who would have to check if there is enough money available in the checking account and if there is, prepare the payment request for human approval. After the boss decides whether to accept the discounted order based on the profit margins, the boss would ask customer service, who would use create_draft to write the customer service response. 
> Preserve all existing project files and functionality and implement only what is required for Problem 6.
> Log this prompt in AI_prompts.md under Problem 6: Plan the three tickets

---

## Problem 7: Backend routes

**Prompt:**

> This is for Problem 7: Backend routes
> In backend/main.py use FastAPI to add the backend routes. Reuse the existing agent team, the mcp tools, working database, audit trail, and reset functionality.
> Add routes to return tickets 101, 102, and 103 with their open or resolved status; run the agent team on a given ticket ID; return agent events showing what agents said, delegated, which tools were used; approve a pending payment or purchase after a human clicks approve (this route is what actually changes cash, the approve route must require a human approver and name); return the current checking balance from cash_accounts; and reset data/campus_customs_new.db to the original values (running a ticket shouldn’t reset the database, reset just happens through the reset route). 
> Make sure the backend can be started from backend/ with “uvicorn main:app --reload --port 8000”
> Update output/harness.md with each route in one line as METHOD /route – what it does
> Don’t build the frontend yet. 
> Test the routes but don’t do a full ticket resolution run. 
> Preserve all existing project files and functionality and implement only what is required for Problem 7.
> Log this prompt in AI_prompts.md under Problem 7: Backend routes

---

## Problem 8: Agent dashboard

**Prompt:**

> This is for Problem 8: Agent dashboard
> Build the frontend dashboard in frontend/ using React + Vite + TypeScript. It should call the FastAPI backend at http://localhost:8000. On the backend allow the Vite page origin (http://localhost:5173) so the browser is allowed to call the routes. 
> The dashboard should list all three tickets and show whether each is open or resolved, let the user select one ticket and start the agent team on it, show the agents’ activity while the ticket runs (like what each agent is saying/doing and which tools and delegations are used), mark a ticket resolved when its run is finished, show a short summary of what each agent did on the selected ticket, show pending payment or purchase requests and let a human approve them through the backend approval route, show the current checking account balance and refresh it after an approved payment.  
> Make the dashboard polished, not plain. Make sure there are clear visual distinctions between agents, ticket status, payment approvals, and cash information. 
> Design choices:
> I want the dashboard to look like an office with all the details. This is because the agents are like coworkers in an office at a company. 
> The floorplan should be viewed from above, the agents should get their own desks with brass nameplates and when that agent is active, their lamp should turn on and they should visibly be working diligently. When someone delegates, there should be a paper airplane that flies to them. The agent messages should be on colorful sticky notes (each agent has their own color).
> The tickets should live in trays, with an “In” tray for the open tickets and a “Done” tray for the resolved ones. A resolved ticket should visually drop into the done tray with a stamp-type effect. 
> The human signature part should be in the form of a paper check that slides into the frame and the human should be able to type their name in to approve the payment. The cash should be in a cash box and should display the remaining balance. There should be an office clock on the wall which shows the shop date.
> Verify that all text is actually readable and not cramped just to fit the design. 
> Showing the agents at their desks visually shows who is working when. The letter trays, check, clock, and cash box are familiar office objects so the design would give the sense that the user is in a real office with real employees.
> Don’t use any external images. 
> The frontend should start with “npm run dev” 
> Create output/design.md which explains the dashboard design choices I described to you. 
> Test the dashboard but don’t do a full ticket resolution run
> Preserve all existing project files and functionality and implement only what is required for Problem 8.
> Log this prompt in AI_prompts.md under Problem 8: Agent dashboard

**Follow-up prompt:**

> This is a follow up to Problem 8: Agent dashboard. Sure add a reset button to the dashboard that calls the existing backend reset route. Ask the user to confirm if they’re sure before resetting, disable the button while the ticket resolution is running, and refresh the tickets, cash box, and pending approvals after the reset. Style the reset button to match the office theme.
> Preserve all existing project files and functionality.
> Log this prompt in AI_prompts.md under Problem 8: Agent dashboard

*What was lacking:* The original prompt had no way to restore the starting data from the dashboard, so tickets could not be rerun without calling the reset route by hand.

---

## Problem 9: Resolve the tickets

**Prompt (Part 1):**

> This is for Problem 9 (part 1): Resolve the tickets
> Start the backend and frontend so I can run the tickets on the dashboard myself. Don’t run any tickets or approve anything since I’ll do that in the dashboard.
> In the dashboard I will reset data/campus_customs_new.db to the original starting values and record the starting checking balance. Then I will run tickets 101, 102, and 103 through the agent team until each one is resolved using the real agent flow, the mcp tools, the human approval, the dashboard/backend behavior we already implemented.
> I will approve the payments myself. Agents may only prepare requests but the human approval step is the only one that can actually change cash, which should be reflected on the front end with the live updated cash balance on the cash box.
> Log this prompt in AI_prompts.md under Problem 9: Resolve the tickets

**Prompt (Part 2):**

> This is for Problem 9 (part 2): Resolve the tickets
> I reset data/campus_customs_new.db and ran tickets 101, 102, and 103 on the dashboard. I approved the payments myself. Don’t reset, rerun the tickets, or approve anything. Use the audit trail, database, and backend routes as the record of what happened and as a reminder never invent anything in the outcomes. 
> Update output/desk_tickets.html. Keep each ticket’s expected section and fill the actual section with which agents worked on the ticket, what they delegated, which mcp tools they used and the final outcome. 
> Fill the cash tab in output/desk_tickets.html with starting checking balance after reset; for each ticket, the cash change caused by resolving it, including what payment caused it and the dollar amount; and the ending checking balance. These values must be computed accurately and precisely so don’t estimate or infer any cash math. 
> Verify the ending checking balance exactly matches cash_accounts in data/campus_customs_new.db. 
> Also create output/resolved_tickets.json containing (for each ticket), id, final status, short outcome, what each agent contributed, and any human approvals that were required.
> Create output/resolved_board.html containing a screenshot of the React dashboard for each resolved ticket 101, 102, and 103. 
> Append the real runs to output/audit_trail.json
> Finish output/harness.md so it covers the tables, mcp tools, five agents, api routes, dashboard, and safety rules. 
> Preserve all existing project files and functionality and implement only what is required for Problem 9.
> Log this prompt in AI_prompts.md under Problem 9: Resolve the tickets

**Follow-up prompt:**

> Fix the two dashboard issues you found. Count only successful payment requests in the agent summary cards and render the agents’ markdown bold as bold instead of showing literal asterisks. Then retake the screenshots in output/resolved_board.html the same read only way. Don’t reset, rerun the tickets, or approve anything. Before and after the fix, confirm that checking is still $160.00, that all three tickets are still resolved and the audit trail has no new runs or approvals.
> Log this prompt in AI_prompts.md under Problem 9: Resolve the tickets

*What was lacking:* The dashboard summary counted rejected payment-request calls as filed requests and showed the agents' markdown bold markers as literal asterisks, so the Part 2 screenshots were partly misleading.

**Follow-up prompt:**

> In output/desk_tickets.html, the delegations table in the Actual sections is wider than its card so the “Task or reason” text runs past the card’s right side edge. Make all tables and text stay inside the Actual card. Make sure you don’t change any wording and keep the Expected sections verbatim.
> Log this prompt in AI_prompts.md under Problem 9: Resolve the tickets

*What was lacking:* The earlier layout fix stopped mid-word breaks but let long slash-joined words in the delegation tasks force the table wider than its card.

---

## Problem 10: Reflection

**Prompt:**

> This is for Problem 10: Reflection
> Please fill in the Reflection tab in output/desk_tickets.html with my text below verbatim (no revising whatsoever):
> For ticket 101, the actual behavior was close to what I expected. I expected the boss to recognize ticket 101 as an inventory problem, send to inventory, have inventory discover the stock shortage and blocked vendor problem, and then involve the accounting agent because invoice 501 had to be paid before Bulldog Print Co could restock the items. 
> That is essentially what happened but the boss executed differently. The boss sent work to inventory, accounting, and customer service at once. Inventory correctly found that there was an inventory shortage and that Bulldog Print Co was blocked by the overdue invoice. After the boss asked a second time, accounting correctly confirmed that paying the invoice was an affordable decision with $3,400 in the checking balance and created the payment request for human approval. Customer service also provided a draft that didn’t overpromise or promise a specific restock date which is more cautious than my expected plan. 
> The main inefficiencies were that inventory and customer service both tried to delegate to the boss which was stopped by the loop safeguard but I found the reasoning to be solid. 
> For ticket 102 the actual behavior matched my plan closely. The boss recognized that rent belonged to the facilities agent. Facilities called accounting to determine whether the payment was affordable and then verified the lease details and recommended paying before the due date. Accounting then created the rent payment request for human approval. I feel this division of labor was logical. 
> There was one error with timing. I approved the payment while the agent run was still finishing, but the boss checked the payment state just slightly earlier. As a result the boss’ final note said the payment was pending even though the database already showed the rent as paid. However, the underlying transaction was correct, so I view this as a minor error. 
> Ticket 103 differed most from my expectation though the result was understandable and logical. I expected accounting to first evaluate the proposed discounted price, then inventory to check stock. However, it seems the boss again delegated to the inventory agent, accounting agent and customer service agent in parallel. 
> The inventory correctly found that only 8/20 hoodies were available and 12 more were needed. It also recognized that Bulldog Print Co was no longer blocked because ticket 101’s invoice was paid. 
> Accounting couldn’t calculate the discounted margin because no actual proposed discount price was supplied. This exposed an assumption in my Expected section since I assumed that the proposed discounted price would be available during the run. Accounting also correctly discovered that campus customs could not afford the restock cost with only $160 remaining. I was impressed that the agents grounded their reasoning so closely with the database since the situation had changed after tickets 101 and 102 and the agents correctly reasoned about the new cash balance and the unblocked vendor. 
> I think this process could potentially have been simpler with one agent and tools. I think a single agent with access to all the mcp tools could have been simpler technically. For ticket 102 for example I think one agent could have called the check_rent_obligation and checked the cash balance, created the payment request and summarized. 
> I wonder if using one agent vs. all five improves or muddles precision since each one is working with a slightly different picture of the state. Maybe the multi agent approach would be more useful for a larger and more specialized team.
> 3 problems the team could solve: the team could fulfill an order for an item that is in stock, like only 3 hoodies. The inventory would confirm the stock and customer service could draft a confirmation. The team could also restock a low-cost item even with the $160 balance. Accounting would check the cash balance and create a purchase order. I could also request to pay next month’s rent. I believe facilities could check the price from the lease and accounting could report that there are insufficient funds to cover the $2,400 rent. 
> I think the team could not solve something involving incoming money like collecting a customer payment since only the cash outflows are modeled and there aren’t tools to record money coming in. So the shop can’t yet earn money. I would add a tool that records customer payments that come in and it would be used by the accounting agent. The team would currently not be able to actually contact anyone since everything stays as a draft and there are several safeguards against sending a message to a real person. I would create a send tool that only sends a draft after a human approves it, used by the customer service agent. The team also would not be able to handle receiving a restock because there is no tool that increases inventory. So even if they received a restocking, they would not be able to record it. I would add a tool that adds stock when a purchase order arrives. This would be used by inventory to record shipments and increase inventory. 
> Log this prompt in AI_prompts.md under Problem 10: Reflection

---

## Setup: Git and GitHub

**Prompt:**

> Please set up git and GitHub on this computer. Install the GitHub CLI if it is missing and then start “gh auth login” with the BROWSER login option so I can sign in. Do not create a repo, do not commit anything, do not push anything yet.

**Follow-up prompt:**

> Run gh auth setup-git so git uses my GitHub sign in. Then set my global git name to “J Yum” and email to [jennifersyum@gmail.com]. Do not create a repo, do not commit, do not push anything yet

*What was lacking:* The first setup prompt signed in to GitHub but did not connect git to that sign-in or set a commit name and email.

**Follow-up prompt:**

> set my git email to 45499262+jsyum@users.noreply.github.com

*What was lacking:* The earlier setup used a personal email address, which would be published in commits to a public repository.

---

## Problem 11: Submit to GitHub

**Prompt (Part 1):**

> This is for Problem 11 (part 1): Submit to GitHub
> Log this prompt in AI_prompts.md under Problem 11: Submit to GitHub
> Prepare this project for submission to a public GitHub repository. 
> Before committing, please make sure the real .env is excluded and never committed or exposed anywhere. Make sure both of the database files are included, the original campus_customs.db and the working campus_customs_new.db. Update .gitignore if necessary. Make sure the .env is excluded and the database files are NOT excluded. 
> Check that no API keys are present in any of the files. 
> Make sure .env.example lists OPENAI_API_KEY with a placeholder value only, never a real key. 
> Update the README so a grader can easily reproduce the project. Also make sure to include the detail about how per Professor Zaman who provided an OpenAI API key because of a Portkey access issue, model calls go directly to OpenAI instead of Portkey. Include instruction for copying/resetting the original database to the working copy for a clean run, starting the mcp server, starting the FastAPI backend, starting the React dashboard, and resetting the database before a full ticket resolution run. 
> Here is the MINIMUM expected file structure. Don’t move, rename or delete any existing files to match it. just check that nothing is missing:
> hw5/
> ├── AI_prompts.md
> ├── requirements.txt
> ├── .env.example
> ├── .gitignore
> ├── .mcp.json
> ├── README.md
> ├── data/
> │   ├── campus_customs.db
> │   └── campus_customs_new.db
> ├── mcp_server/
> │   ├── server.py
> │   └── README.md
> ├── frontend/
> ├── backend/
> │   ├── main.py
> │   ├── models.py
> │   └── prompts/
> │       ├── boss.md
> │       ├── inventory.md
> │       ├── accounting.md
> │       ├── facilities.md
> │       └── customer_service.md
> └── output/
>     ├── harness.md
>     ├── mcp_smoke.json
>     ├── desk_tickets.html
>     ├── design.md
>     ├── resolved_tickets.json
>     ├── resolved_board.html
>     ├── audit_trail.json
>     └── github_url.txt
> Show me exactly which files will be committed. Don’t create the repo or push yet.

**Prompt (Part 2):**

> This is for Problem 11 (part 2): Submit to GitHub
> Log this prompt in AI_prompts.md under Problem 11: Submit to GitHub
> Create a public GitHub repository for this project under my account, called hw5, push it and put the repo URL in output/github_url.txt. You can commit and push that file too and give me the url.
