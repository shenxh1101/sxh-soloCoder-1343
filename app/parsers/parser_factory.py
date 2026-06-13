from app.parsers.python_parser import PythonParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.java_parser import JavaParser
from app.parsers.cpp_parser import CppParser
from app.config import Config

class ParserFactory:
    _parsers = {
        'python': PythonParser,
        'javascript': JavaScriptParser,
        'java': JavaParser,
        'cpp': CppParser
    }

    @staticmethod
    def get_parser(language):
        parser_class = ParserFactory._parsers.get(language)
        if parser_class:
            return parser_class()
        return None

    @staticmethod
    def get_language_by_extension(extension):
        for lang, exts in Config.SUPPORTED_LANGUAGES.items():
            if extension in exts:
                return lang
        return None

    @staticmethod
    def get_parser_by_extension(extension):
        language = ParserFactory.get_language_by_extension(extension)
        if language:
            return ParserFactory.get_parser(language)
        return None

    @staticmethod
    def get_supported_languages():
        return list(ParserFactory._parsers.keys())

    @staticmethod
    def get_supported_extensions():
        extensions = []
        for exts in Config.SUPPORTED_LANGUAGES.values():
            extensions.extend(exts)
        return extensions
