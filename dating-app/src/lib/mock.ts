import type { Match, Profile } from "@/lib/types";

export const mockProfiles: Profile[] = [
  {
    id: "p1",
    name: "Ava",
    age: 27,
    bio: "Coffee walks, museums, and trying one new recipe a week.",
    city: "Seattle",
    interests: ["coffee", "museums", "cooking", "hiking"],
  },
  {
    id: "p2",
    name: "Noah",
    age: 29,
    bio: "Weekend climber. Weekday spreadsheets. Always down for ramen.",
    city: "San Francisco",
    interests: ["climbing", "ramen", "live music"],
  },
  {
    id: "p3",
    name: "Mia",
    age: 25,
    bio: "Bookstores > bars. Tell me your favorite small win this week.",
    city: "Austin",
    interests: ["reading", "dogs", "film"],
  },
];

export const mockMatches: Match[] = [
  {
    id: "m1",
    profile: mockProfiles[0]!,
    lastMessagePreview: "Museum this weekend?",
  },
  {
    id: "m2",
    profile: mockProfiles[2]!,
    lastMessagePreview: "That’s such a good book rec.",
  },
];

