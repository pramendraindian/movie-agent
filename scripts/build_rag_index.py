import argparse

from app.services.vector_index_service import get_vector_index_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local RAG movie index")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing index entries before indexing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional cap for number of movies to index",
    )
    args = parser.parse_args()

    service = get_vector_index_service()
    stats = service.build_index(rebuild=args.rebuild, limit=args.limit or None)
    print(
        f"Indexed {stats.indexed_movies} / {stats.total_movies} movies into local ChromaDB"
    )


if __name__ == "__main__":
    main()
