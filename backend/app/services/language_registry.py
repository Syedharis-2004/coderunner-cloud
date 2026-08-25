from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LanguageConfig:
    """Defines all parameters for executing a specific language in Docker."""
    key: str
    display_name: str
    version: str
    image: str
    source_filename: str
    run_cmd: str
    compile_cmd: Optional[str] = None
    default_template: str = ""
    monaco_language: str = "plaintext"
    timeout_override: Optional[int] = None
    memory_limit_override: Optional[str] = None


class LanguageRegistry:
    """
    Central registry for all supported sandboxed runtimes.
    Adding a new language requires ONLY adding a new entry here —
    no changes to the execution engine itself.
    """

    _languages: Dict[str, LanguageConfig] = {
        "python": LanguageConfig(
            key="python",
            display_name="Python",
            version="3.11",
            image="python:3.11-slim",
            source_filename="main.py",
            run_cmd="python main.py",
            monaco_language="python",
            default_template="""# CodeRunner Cloud — Python 3.11
import sys

def main():
    name = "World"
    print(f"Hello, {name} from CodeRunner Cloud!")
    print(f"Python version: {sys.version.split()[0]}")

if __name__ == '__main__':
    main()
""",
        ),
        "javascript": LanguageConfig(
            key="javascript",
            display_name="JavaScript (Node.js)",
            version="20 LTS",
            image="node:20-alpine",
            source_filename="main.js",
            run_cmd="node main.js",
            monaco_language="javascript",
            default_template="""// CodeRunner Cloud — Node.js 20
function main() {
    console.log("Hello from Node.js on CodeRunner Cloud!");
    console.log("Node version: " + process.version);
}

main();
""",
        ),
        "cpp": LanguageConfig(
            key="cpp",
            display_name="C++ (GCC 13)",
            version="C++20",
            image="gcc:13-bookworm",
            source_filename="main.cpp",
            compile_cmd="g++ -O2 -std=c++20 main.cpp -o main_bin",
            run_cmd="./main_bin",
            monaco_language="cpp",
            # C++ needs more compile time, so a slight timeout bump
            timeout_override=30,
            default_template="""// CodeRunner Cloud — C++20
#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::cout << "Hello from C++20 on CodeRunner Cloud!" << std::endl;
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = std::accumulate(numbers.begin(), numbers.end(), 0);
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}
""",
        ),
        "typescript": LanguageConfig(
            key="typescript",
            display_name="TypeScript (Deno)",
            version="Deno 1.x",
            image="denoland/deno:alpine",
            source_filename="main.ts",
            run_cmd="deno run --no-check main.ts",
            monaco_language="typescript",
            default_template="""// CodeRunner Cloud — TypeScript (Deno)
function greet(name: string): void {
    console.log(`Hello, ${name} from CodeRunner Cloud!`);
}

greet("TypeScript");
""",
        ),
        "csharp": LanguageConfig(
            key="csharp",
            display_name="C# (.NET 8)",
            version="8.0",
            image="mcr.microsoft.com/dotnet/sdk:8.0-alpine",
            source_filename="main.cs",
            compile_cmd=(
                "dotnet new console -o app -f net8.0 --force "
                "&& cp main.cs app/Program.cs "
                "&& cd app && dotnet build -c Release -o out"
            ),
            run_cmd="./app/out/app",
            monaco_language="csharp",
            timeout_override=60,
            default_template="""// CodeRunner Cloud — C# (.NET 8)
using System;

class Program
{
    static void Main()
    {
        Console.WriteLine("Hello from C# on CodeRunner Cloud!");
    }
}
""",
        ),
    }

    @classmethod
    def get(cls, key: str) -> Optional[LanguageConfig]:
        """Look up a language config by key (case-insensitive)."""
        return cls._languages.get(key.lower().strip())

    @classmethod
    def list_all(cls) -> List[Dict]:
        """Return all registered languages as a list of dicts for the API."""
        return [
            {
                "key": lang.key,
                "display_name": lang.display_name,
                "version": lang.version,
                "monaco_language": lang.monaco_language,
                "default_template": lang.default_template,
            }
            for lang in cls._languages.values()
        ]

    @classmethod
    def is_supported(cls, key: str) -> bool:
        return cls.get(key) is not None


language_registry = LanguageRegistry()
