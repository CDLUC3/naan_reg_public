"""
Copyright©2024, Regents of the University of California

License: https://opensource.org/license/mit, See LICENSE

Manage JSON embedded in GH issues.

"""
import json
import os
import re
import typing

import gql
import gql.transport.requests

RE_EXTRACT_JSON = re.compile(r"\`\`\`json([\s\S]*?)\`\`\`", re.DOTALL)


def extract_json_block_from_markdown(
        markdown: str,
) -> typing.Optional[typing.Union[typing.Dict, typing.List]]:
    data_match = RE_EXTRACT_JSON.search(markdown)
    if data_match is None:
        return None
    data_str = data_match.group(1)
    data = json.loads(data_str)
    return data


class IssueJsonExtractor:
    """
    Extracts a JSON block from a github issue description.

    Loosely based on https://github.com/peter-murray/issue-body-parser-action
    """

    def __init__(self, user: str, repo: str):
        self.user = user
        self.repo = repo
        headers = {"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN')}"}
        print(headers)
        transport = gql.transport.requests.RequestsHTTPTransport(
            url=os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"),
            headers=headers,
            timeout=10,
        )
        self.client = gql.Client(transport=transport)
        # GITHUB_REPOSITORY_ID is set when running in a workflow
        self.repository_id = os.environ.get("GITHUB_REPOSITORY_ID", None)
        if self.repository_id is None:
            # if not set, then use graphql to get the repository_id
            self.repository_id = self.get_repository_id()

    def get_repository_id(self):
        q = gql.gql(
            """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                name
                id
            }
        }"""
        )
        params = {"owner": self.user, "repo": self.repo}
        result = self.client.execute(q, variable_values=params)
        return result.get("repository", {}).get("id", None)

    def list_projects(self):
        q = gql.gql(
            """
         query($owner: String!, $repo: String!) {
             repository(owner:$owner, name:$repo) {
                 name
                 url
                 projectsV2(first: 5) {
                     edges {
                         node {
                             id
                             title
                         }
                     }
                 } projects(first: 5) {
                     edges {
                         node {
                             id
                             name
                         }
                     }
                 }
             }
         }"""
        )
        params = {"owner": self.user, "repo": self.repo}
        result = self.client.execute(q, variable_values=params)
        return result

    def get_issue(self, issue_number: int) -> dict:
        q = gql.gql(
            """
        query($owner: String!, $repo: String!, $issue_number: Int!) {
            repository(name: $repo, owner: $owner) {
                issue(number:$issue_number) {
                    id
                    title
                    createdAt
                    body
                }
            }
        }"""
        )
        params = {"owner": self.user, "repo": self.repo, "issue_number": issue_number}
        result = self.client.execute(q, variable_values=params)
        return result

    def get_json_from_issue(
            self, issue_number: int, key: str = None
    ) -> typing.Optional[typing.Dict]:
        issue = self.get_issue(issue_number)
        body = issue.get("repository", {}).get("issue", {}).get("body", "")
        data = extract_json_block_from_markdown(body)
        return data

    def add_comment_to_issue(self, issue_number: int, comment: str) -> None:
        issue = self.get_issue(issue_number)
        q = gql.gql(
            """
            mutation($subjectId:ID!, $body:String!) {
                addComment(input:{subjectId: $subjectId, body: $body}) {
                    commentEdge {
                        node {
                            createdAt
                            body
                        }
                    }
                }
            }
            """
        )
        params = {
            "subjectId": issue.get("repository", {}).get("issue", {}).get("id", None),
            "body": comment,
        }
        result = self.client.execute(q, variable_values=params)
        print(result)

    def get_label_id(self, label_name: str) -> typing.Optional[str]:
        q = gql.gql(
            """
            query
            """
        )

    def add_label_to_issue(self, issue_number: int, label: str) -> None:
        issue = self.get_issue(issue_number)
        q = gql.gql(
            """
            mutation($subjectId:ID!, $body:String!) {
                addComment(input:{subjectId: $subjectId, body: $body}) {
                    commentEdge {
                        node {
                            createdAt
                            body
                        }
                    }
                }
            }
            """
        )
        params = {
            "subjectId": issue.get("repository", {}).get("issue", {}).get("id", None),
            "body": label,
        }
        result = self.client.execute(q, variable_values=params)
        print(result)
