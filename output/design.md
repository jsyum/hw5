# Dashboard Design

The Campus Customs dashboard (`frontend/`, React + Vite + TypeScript) shows the agent team as coworkers in a real office. The agents are like employees at a company, so the dashboard looks like the room they work in. Every element is a familiar office object, so a person can read what is happening at a glance, without learning a new interface.

## Why an office

- **Agents are coworkers.** Each agent has a role, a desk, and a nameplate, like an employee. Seeing who is at work makes it obvious who is responsible for what.
- **Familiar objects carry meaning.** Letter trays, a paper check, a wall clock, and a cash box each already mean something to anyone who has worked in an office. The dashboard borrows that meaning instead of inventing icons.
- **Real money and real customers stay human.** The payment step looks like signing a physical check, which signals that a person, not an agent, is authorizing money.

## The floor plan

- **Top-down view.** The office is drawn from above, like an architect's floor plan. The Boss's desk sits on a red rug at the head of the room, and the four specialists sit in two rows below.
- **Desks and brass nameplates.** Each agent has a wooden desk with a monitor, keyboard, papers, a mug, and a brass nameplate engraved with its name.
- **Lamps show who is active.** When an agent is active, its desk lamp turns on and casts a warm glow. The monitor lights up, lines of text type across the screen, the keyboard flickers, the pen writes, and the agent bobs in its chair, so it is visibly working diligently. An agent waiting on a teammate keeps its lamp on but dimmer, and its status card shows a purple "Waiting" dot.
- **Status cards.** Under each desk, a card with the agent's color stripe says Working, Waiting, or Idle, and what the agent is doing right now, such as "Using check_order_fulfillment".
- **Paper airplanes for delegation.** When one agent delegates to another, a paper airplane flies from the sender's desk to the receiver's, with a small label such as "Boss → Inventory".

## Sticky notes

Agent messages appear on a cork board as sticky notes. Each agent has its own color, also used for its chair and summary card:

| Agent | Note color |
|---|---|
| Boss | Yellow |
| Inventory | Green |
| Accounting | Blue |
| Facilities | Orange |
| Customer Service | Pink |

Notes show what the agent said, which tools it used, and whom it asked for help. Long notes collapse with a "Read all" link, so text is never shrunk to fit.

## Ticket trays

- **In and Done.** Open tickets sit in the "In" letter tray and resolved tickets in the "Done" tray. Each ticket is a paper slip with its number, subject, requester, and a colored status pill: blue for Open, amber for Agents working, green for Resolved.
- **Drop and stamp.** When a run finishes, the ticket drops into the Done tray and a red "RESOLVED" rubber stamp slams onto it. The stamp has its own space on the slip so it never covers text.
- **Folder.** The selected ticket opens in a manila folder with its details and the "Start agent team" button.

## The check

When an agent files a payment or purchase request, a paper check slides into the frame from the right. It shows the payee, the amount in numbers and words, a memo with the ticket and reason, and which agent requested it. The human approves by typing their name on the signature line, which renders in script, and pressing "Sign & approve". A green "PAID" stamp lands on the check and it slides away. "Not now" tucks it into a small tab without approving. The check goes through the backend approval route, which is the only path that moves money.

## Cash box and clock

- **Cash box.** A steel cash box shows the checking balance on a bright display, with the amount awaiting approval and the cash left after approvals. After a payment is approved, the balance counts down and the display flashes.
- **Wall clock.** A clock on the wall ticks in real time, and its date window and brass plaque show the shop date from `desk.date_today`, which is the date the agents use for every due-date decision.

## Reset button

The reset control is a red push button mounted on a brass wall plate, like an office's emergency or building control, so it reads as a deliberate, room-wide action rather than an ordinary button. Pressing it pins a paper memo to the screen that explains what a reset restores and asks "Reset the office?", with "Yes, reset everything" and "Cancel". While the agents are working, the button turns gray and the plate reads "Locked while agents work". After a reset, the trays, cash box, and pending checks refresh to the starting data.

## Readability

- **Text size.** All text is at least 12 px, and body text is 14 to 16 px. Small labels use bold, letter-spaced capitals.
- **Contrast.** Sticky notes always pair a light paper color with dark ink in the same hue. Text on wood, cork, or steel sits on its own light or dark panel.
- **Nothing cut off.** Long text wraps or expands instead of being cut off. Testing at 1500, 1280, 900, and 420 px wide found no clipped text and no sideways scrolling.
- **No external images.** Every object is drawn with CSS and inline SVG.
- **Reduced motion.** Animations respect the system's reduced-motion setting.
