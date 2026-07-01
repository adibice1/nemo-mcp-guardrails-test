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

export const mockPolicyOptions = [
  {
    value: "github",
    label: "GitHub",
    actions: [
      { value: "create", label: "Create", resources: [
        { value: "branch", label: "Branch" },
        { value: "file", label: "File" },
        { value: "issue", label: "Issue" },
        { value: "pull_request", label: "Pull Request" },
        { value: "repository", label: "Repository" }
      ] },
      { value: "update", label: "Update", resources: [
        { value: "file", label: "File" },
        { value: "issue", label: "Issue" },
        { value: "pull_request", label: "Pull Request" }
      ] },
      { value: "delete", label: "Delete", resources: [
        { value: "file", label: "File" }
      ] },
      { value: "merge", label: "Merge", resources: [
        { value: "pull_request", label: "Pull Request" }
      ] },
      { value: "review", label: "Review", resources: [
        { value: "pull_request", label: "Pull Request" }
      ] },
      { value: "comment", label: "Comment", resources: [
        { value: "issue", label: "Issue" }
      ] },
      { value: "fork", label: "Fork", resources: [
        { value: "repository", label: "Repository" }
      ] },
      { value: "push", label: "Push", resources: [
        { value: "file", label: "File" }
      ] },
      { value: "search", label: "Search", resources: [
        { value: "file", label: "File" },
        { value: "issue", label: "Issue" },
        { value: "pull_request", label: "Pull Request" },
        { value: "repository", label: "Repository" }
      ] },
      { value: "list", label: "List", resources: [
        { value: "branch", label: "Branch" },
        { value: "commit", label: "Commit" },
        { value: "issue", label: "Issue" },
        { value: "issue_type", label: "Issue Type" },
        { value: "pull_request", label: "Pull Request" },
        { value: "release", label: "Release" },
        { value: "tag", label: "Tag" }
      ] },
      { value: "read", label: "Read", resources: [
        { value: "commit", label: "Commit" },
        { value: "file", label: "File" },
        { value: "issue", label: "Issue" },
        { value: "label", label: "Label" },
        { value: "pull_request", label: "Pull Request" },
        { value: "release", label: "Release" },
        { value: "tag", label: "Tag" }
      ] }
    ]
  }
];
