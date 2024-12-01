FROM python:3.13-bookworm as base

FROM base as builder
COPY . /app
WORKDIR /app
RUN pip install --root-user-action=ignore --break-system-packages poetry && poetry install --only main
RUN poetry self add poetry-plugin-export
RUN poetry export -n --without-hashes --output=requirements.txt
RUN poetry build -n --format=wheel

FROM base as final
COPY --from=builder /app/requirements.txt /requirements.txt
COPY --from=builder /app/dist /dist
RUN pip install --root-user-action=ignore --break-system-packages -r /requirements.txt
RUN pip install --root-user-action=ignore /dist/*.whl

EXPOSE 80
WORKDIR /

ENTRYPOINT [ "/bin/sh", "-c", "mac-server -P 80 ${@}", "--" ]
