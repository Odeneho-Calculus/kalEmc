from rich.tree import Tree
from rich.console import Console
from pathlib import Path

def build_tree(path: Path, tree: Tree):
    for entry in sorted(path.iterdir()):
        if entry.name.startswith('.'):
            continue
        branch = tree.add(f"[bold]{entry.name}[/]" if entry.is_dir() else entry.name)
        if entry.is_dir():
            build_tree(entry, branch)

def main(root_dir="."):
    path = Path(root_dir)
    tree = Tree(f"[bold magenta]{path.resolve().name}[/]")
    build_tree(path, tree)
    console = Console()
    console.print(tree)

if __name__ == "__main__":
    import sys
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    main(root_dir)
