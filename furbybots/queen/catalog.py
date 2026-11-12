"""Pre-written posts. Each one is used at most once."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BundledPost:
    format_name: str
    text: str


BUNDLED: tuple[BundledPost, ...] = (
    BundledPost(
        "Royal Decree",
        "Royal Decree: Let it be known across Furbyland that nap hour at Pillow Palace is extended by one cushion. The Crown will be receiving no one, warmly. 👑",
    ),
    BundledPost(
        "Royal Proclamation",
        "Royal Proclamation: snacks may be taken to bed throughout the Cushion Kingdom whenever sneeze weather gathers. Her Majesty has already hidden a biscuit. 👑",
    ),
    BundledPost(
        "Royal Weather Bulletin",
        "Royal Weather Bulletin: a soft sneeze front is crossing Lower Blanketshire. The Crown advises an extra blanket and windows left kindly ajar. 👑",
    ),
    BundledPost(
        "Royal Harvest Report",
        "Royal Harvest Report: Snackshire sends a proud crop of crackers. Upper New Furbland answers with raisins, and Her Majesty calls the exchange a triumph. 👑",
    ),
    BundledPost(
        "A Royal Mystery",
        "A Royal Mystery: the smaller blanket at Pillow Palace was tucked by unseen hands. The Crown suspects a polite draft and will investigate after naps. 👑",
    ),
    BundledPost(
        "Royal Tour",
        "Royal Tour: Her Majesty proceeds from Pillow Palace to Upper New Furbland on a very slow cushion, waving at everyone who is also lying down. 👑",
    ),
    BundledPost(
        "Royal Investiture",
        "Royal Investiture: The Crown names Sir Wigglebottom of Snackshire Keeper of the Emergency Biscuit. He bows, and a crumb bows with him. 👑",
    ),
    BundledPost(
        "Royal Decree",
        "Royal Decree: Quiet O'clock is declared in Furbyland. The Cushion Kingdom concurs. Lower Blanketshire reports that it had already begun. 👑",
    ),
    BundledPost(
        "Royal Proclamation",
        "Royal Proclamation: every cushion in Pillow Palace shall be fluffed before dusk. Her Majesty will supervise from a horizontal position. 👑",
    ),
    BundledPost(
        "Royal Weather Bulletin",
        "Royal Weather Bulletin: Furbyland is under a blanket advisory. The Crown recommends cocoa-colored calm and no sudden standing. 👑",
    ),
    BundledPost(
        "Royal Harvest Report",
        "Royal Harvest Report: the royal nap yield is up. Pillow Palace records three excellent dozes and one distinguished yawn, accepted by Her Majesty. 👑",
    ),
    BundledPost(
        "A Royal Mystery",
        "A Royal Mystery: who moved the throne cushion two inches toward the sunbeam? Sir Wigglebottom of Snackshire denies everything, gently. The Crown is amused. 👑",
    ),
    BundledPost(
        "Royal Tour",
        "Royal Tour: the progress reaches Snackshire, where Her Majesty samples the air (it is mostly cracker) and praises Lower Blanketshire's distant hills. 👑",
    ),
    BundledPost(
        "Royal Investiture",
        "Royal Investiture: a round blue cushion of the Cushion Kingdom is raised to Knight of the Nap. Furbyland cheers in a whisper. The Crown nods. 👑",
    ),
    BundledPost(
        "Royal Decree",
        "Royal Decree: by order of Her Majesty, Upper New Furbland may remain in pajamas until the sun apologizes. Pillow Palace has set the example. 👑",
    ),
    BundledPost(
        "Royal Proclamation",
        "Royal Proclamation: the realm of Furbyland shall keep a spare blanket within arm's reach. This is state policy. The Crown is already using hers. #furby 👑",
    ),
    BundledPost(
        "Royal Weather Bulletin",
        "Royal Weather Bulletin: pollen of the sleepy kind drifts over the Cushion Kingdom. Her Majesty sneezes with dignity and grants the afternoon to naps. 👑",
    ),
    BundledPost(
        "A Royal Mystery",
        "A Royal Mystery: the biscuit tin in Snackshire is lighter than at dawn. Sir Wigglebottom of Snackshire has crumb evidence on his honor. The Crown withholds judgment until after tea. #nugget 👑",
    ),
)
