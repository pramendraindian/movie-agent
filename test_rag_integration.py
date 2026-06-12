import unittest
from unittest.mock import patch

from app.services.intent_service import get_intent_response
from app.services.recommendation_service import get_movie_recommendations


class RagIntegrationTests(unittest.TestCase):
    @patch("app.services.intent_service.classify", return_value=("fallback", 0.01))
    @patch("app.services.intent_service.llm_fallback", return_value="legacy fallback")
    @patch("app.services.intent_service.rag_generate_fallback_response")
    @patch("app.services.intent_service.get_rag_config")
    def test_rag_disabled_keeps_legacy_fallback(
        self,
        mock_get_config,
        mock_rag_generate,
        mock_llm_fallback,
        _mock_classify,
    ):
        mock_get_config.return_value = type(
            "Cfg",
            (),
            {
                "enabled": False,
                "fallback_enabled": False,
                "movie_augmentation_enabled": False,
                "fallback_movie_queries_only": False,
            },
        )()

        resp = get_intent_response("what should i watch")

        self.assertIn("response", resp)
        self.assertEqual(resp["response"], "legacy fallback")
        mock_rag_generate.assert_not_called()
        mock_llm_fallback.assert_called_once()

    @patch("app.services.intent_service.classify", return_value=("fallback", 0.01))
    @patch("app.services.intent_service.rag_generate_fallback_response", return_value=None)
    @patch("app.services.intent_service.llm_fallback", return_value="legacy fallback")
    @patch("app.services.intent_service.get_rag_config")
    def test_rag_failure_falls_back_to_legacy_string(
        self,
        mock_get_config,
        mock_llm_fallback,
        _mock_rag_generate,
        _mock_classify,
    ):
        mock_get_config.return_value = type(
            "Cfg",
            (),
            {
                "enabled": True,
                "fallback_enabled": True,
                "movie_augmentation_enabled": False,
                "fallback_movie_queries_only": False,
            },
        )()

        resp = get_intent_response("unknown intent")
        self.assertEqual(resp["response"], "legacy fallback")
        mock_llm_fallback.assert_called_once()

    @patch("app.services.recommendation_service.get_rag_config")
    @patch("app.services.recommendation_service.get_retrieval_service")
    @patch("app.services.recommendation_service.get_recommendation_engine")
    @patch("app.services.recommendation_service.extract_entities", return_value={})
    def test_movie_augmentation_flag_maintains_schema(
        self,
        _mock_entities,
        mock_engine,
        mock_retrieval_service,
        mock_get_config,
    ):
        mock_get_config.return_value = type(
            "Cfg",
            (),
            {
                "enabled": True,
                "movie_augmentation_enabled": True,
            },
        )()

        mock_engine.return_value.get_trending_recommendations.return_value = [
            {
                "title": "Movie A",
                "rating": 8.0,
                "runtime": "120 min",
                "release_year": "2020",
                "genres": "Action",
                "overview": "A",
                "poster_path": "/a.jpg",
            }
        ]

        retrieved = type(
            "Ret",
            (),
            {
                "title": "Movie B",
                "genres": "Drama",
                "overview": "B",
                "rating": 7.5,
                "runtime": "100 min",
                "release_year": "2019",
                "poster_path": "/b.jpg",
                "similarity": 0.8,
            },
        )()
        mock_retrieval_service.return_value.retrieve.return_value = [retrieved]

        response = get_movie_recommendations("something dramatic")
        self.assertIn("response", response)
        self.assertIn("movies", response)
        self.assertIsInstance(response["movies"], list)


if __name__ == "__main__":
    unittest.main()
