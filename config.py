DOCS_SITES = (
    "readthedocs.io",
    "docs.rs",
    "developer.mozilla.org",
    "pkg.go.dev",
    "docs.python.org",
    "docs.spring.io",
    "learn.microsoft.com",
)

CODE_SITES = (
    "github.com",
    "dev.to",
    "developer.mozilla.org",
    "docs.python.org",
    "learn.microsoft.com",
    "reddit.com/r/programming",
    "reddit.com/r/learnprogramming",
)

ERROR_SITES = tuple(dict.fromkeys(CODE_SITES + (
    "reddit.com",
    "askubuntu.com",
    "superuser.com",
    "serverfault.com",
    "discuss.python.org",
    "bugs.python.org",
)))

MAVEN_SITES = (
    "central.sonatype.com",
    "mvnrepository.com",
    "search.maven.org",
    "plugins.gradle.org",
)

SPRING_SITES = (
    "spring.io",
    "docs.spring.io",
    "github.com/spring-projects",
    "github.com/spring-cloud",
    "reflectoring.io",
    "thorben-janssen.com",
    "vladmihalcea.com",
    "piotrminkowski.com",
)
