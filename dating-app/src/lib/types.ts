export type Profile = {
  id: string;
  name: string;
  age: number;
  bio: string;
  city: string;
  interests: string[];
};

export type Match = {
  id: string;
  profile: Profile;
  lastMessagePreview?: string;
};

