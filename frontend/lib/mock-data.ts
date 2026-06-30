export type PolicyRow = {
  id: number | string;
  policyId?: number;
  assignmentId?: number;
  scope?: "app" | "global";
  connector: string;
  name: string;
  created: string;
  global: boolean;
  app: string | null;
};

export const appOptions = ["App A", "App B"];

export const initialPolicies: PolicyRow[] = [
  {
    id: 1,
    connector: "GitHub",
    name: "Create Issue",
    created: "2021-11-04T11:54",
    global: true,
    app: null
  },
  {
    id: 2,
    connector: "GitHub",
    name: "Create Repository",
    created: "2021-11-03T22:00",
    global: true,
    app: null
  },
  {
    id: 3,
    connector: "GitHub",
    name: "Delete Pull Request",
    created: "2021-11-02T11:09",
    global: false,
    app: "App A"
  },
  {
    id: 4,
    connector: "GitHub",
    name: "Update Issue",
    created: "2021-10-31T17:24",
    global: false,
    app: "App A"
  },
  {
    id: 5,
    connector: "GitHub",
    name: "Create Repository",
    created: "2021-10-03T22:00",
    global: false,
    app: "App A"
  },
  {
    id: 6,
    connector: "GitHub",
    name: "Delete Pull Request",
    created: "2021-10-02T11:09",
    global: false,
    app: "App B"
  },
  {
    id: 7,
    connector: "GitHub",
    name: "Update Issue",
    created: "2021-09-31T17:24",
    global: false,
    app: "App B"
  },
  {
    id: 8,
    connector: "GitHub",
    name: "Create Repository",
    created: "2021-09-03T22:00",
    global: false,
    app: "App A"
  },
  {
    id: 9,
    connector: "GitHub",
    name: "Delete Pull Request",
    created: "2021-09-02T11:09",
    global: false,
    app: "App A"
  },
  {
    id: 10,
    connector: "GitHub",
    name: "Update Issue",
    created: "2021-08-31T17:24",
    global: false,
    app: "App B"
  }
];

export const connectorOptions = [
  "GitHub",
  "SharePoint",
  "Outlook",
  "Teams",
  "OneDrive",
  "Jira",
  "Confluence"
];

export const actionOptions = [
  "Create",
  "Update",
  "Delete",
  "Merge",
  "Review",
  "Comment",
  "Fork",
  "Push"
];

export const resourceOptions = [
  "Issue",
  "Pull Request",
  "Repository",
  "Branch",
  "File",
  "Commit",
  "Release",
  "Tag",
  "Comment",
  "Review"
];
