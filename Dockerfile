# linkedin-content-manager has zero runtime dependencies, so a single slim stage
# is enough - there is nothing to compile and nothing to prune between stages.
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 lcm
WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

COPY content ./content
RUN chown -R lcm:lcm /app

USER lcm
ENTRYPOINT ["python", "-m", "linkedin_content_manager"]
CMD ["--help"]
