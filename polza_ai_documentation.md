> ## Documentation Index
> Fetch the complete documentation index at: https://polza.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Быстрый старт

> Начните работу за несколько минут

## Шаг 1: Получите API ключ

1. Зарегистрируйтесь на [polza.ai/dashboard](https://polza.ai/dashboard)
2. Пополните баланс в личном кабинете
3. Создайте API-ключ в разделе [API Keys](https://polza.ai/dashboard/api-keys)

## Шаг 2: Используйте API

<CodeGroup>
  ```typescript TypeScript theme={null}
  import OpenAI from 'openai';

  const openai = new OpenAI({
    baseURL: 'https://polza.ai/api/v1',
    apiKey: '<POLZA_AI_API_KEY>'
  });

  async function main() {
    const completion = await openai.chat.completions.create({
      model: 'openai/gpt-4o',
      messages: [{
        role: 'user',
        content: 'Что думаешь об этой жизни?',
      }],
    });
    console.log(completion.choices[0].message);
  }

  main();
  ```

  ```python Python theme={null}
  from openai import OpenAI

  client = OpenAI(
    base_url="https://polza.ai/api/v1",
    api_key="<POLZA_AI_API_KEY>",
  )

  completion = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{
      "role": "user",
      "content": "Что думаешь об этой жизни?"
    }]
  )

  print(completion.choices[0].message.content)
  ```

  ```bash cURL theme={null}
  curl -X POST "https://polza.ai/api/v1/chat/completions" \
    -H "Authorization: Bearer <POLZA_AI_API_KEY>" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/gpt-4o",
      "messages": [{"role": "user", "content": "Привет!"}]
    }'
  ```
</CodeGroup>

## Шаг 3: Выберите модель

Полный каталог моделей доступен на [polza.ai/models](https://polza.ai/models) или через API:

```bash theme={null}
curl https://polza.ai/api/v1/models
```

### Популярные модели

| Модель            | ID                                  | Описание                  |
| ----------------- | ----------------------------------- | ------------------------- |
| GPT-4o            | `openai/gpt-4o`                     | Флагманская модель OpenAI |
| Claude 3.5 Sonnet | `anthropic/claude-3-5-sonnet`       | Лучшая модель Anthropic   |
| Gemini 2.5 Pro    | `google/gemini-2.5-pro-preview`     | Продвинутая модель Google |
| Llama 3.3 70B     | `meta-llama/llama-3.3-70b-instruct` | Open-source модель Meta\* |

## Следующие шаги

<CardGroup cols={2}>
  <Card title="API Справочник" icon="code" href="/docs/api-reference/chat/completions">
    Изучите полную документацию API
  </Card>

  <Card title="Интеграции" icon="plug" href="/docs/integracii/cline">
    Подключите к вашим инструментам
  </Card>
</CardGroup>

***

\* Meta признана экстремистской организацией и запрещена в Российской Федерации.


> ## Documentation Index
> Fetch the complete documentation index at: https://polza.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# POST Chat Completions

> Основной эндпоинт для генерации текста и диалогов

Поддерживает текстовые диалоги, мультимодальные запросы (текст + изображения + аудио + видео + файлы), вызов функций и потоковую передачу.

## Возможности

* **Агрегация провайдеров** — автоматический выбор оптимального провайдера
* **Биллинг в рублях** — точный учет стоимости
* **Reasoning Tokens** — поддержка моделей с рассуждениями
* **Streaming** — потоковая передача через SSE
* **Tool Calling** — вызов внешних функций
* **Мультимодальность** — обработка текста, изображений, аудио, видео и файлов

## Параметры запроса

### Обязательные

| Параметр | Тип    | Описание                                                  |
| -------- | ------ | --------------------------------------------------------- |
| `model`  | string | ID модели из [списка моделей](/docs/api-reference/models/list) |

### Контент

| Параметр   | Тип    | Описание                                         |
| ---------- | ------ | ------------------------------------------------ |
| `messages` | array  | Массив сообщений диалога (рекомендуется)         |
| `prompt`   | string | Простой текстовый промпт (альтернатива messages) |

### Параметры генерации

| Параметр                | Тип           | По умолчанию | Описание                                        |
| ----------------------- | ------------- | ------------ | ----------------------------------------------- |
| `max_tokens`            | integer       | Без лимита   | Максимум токенов в ответе                       |
| `max_completion_tokens` | integer       | Без лимита   | Альтернатива max\_tokens                        |
| `temperature`           | float (0-2)   | 1.0          | Температура (0=детерминированный, 2=креативный) |
| `top_p`                 | float (0-1)   | 1.0          | Nucleus sampling                                |
| `top_k`                 | integer       | —            | Top-K sampling                                  |
| `frequency_penalty`     | float (-2..2) | 0            | Штраф за повторение слов                        |
| `presence_penalty`      | float (-2..2) | 0            | Штраф за повторение токенов                     |
| `stop`                  | string/array  | —            | Стоп-последовательности                         |
| `seed`                  | integer       | —            | Seed для воспроизводимости                      |

### Специальные возможности

| Параметр             | Тип           | Описание                                                 |
| -------------------- | ------------- | -------------------------------------------------------- |
| `stream`             | boolean       | Включить streaming (SSE)                                 |
| `reasoning`          | object        | Настройки reasoning tokens                               |
| `tools`              | array         | Доступные функции для вызова                             |
| `tool_choice`        | string/object | Выбор инструмента: "none", "auto", "required"            |
| `response_format`    | object        | Формат ответа: text, json\_object, json\_schema, grammar |
| `web_search_options` | object        | Встроенный веб-поиск                                     |
| `provider`           | object        | Конфигурация роутинга по провайдерам                     |
| `plugins`            | array         | Подключение плагинов                                     |
| `modalities`         | array         | Выходные модальности: "text", "image", "audio"           |
| `audio`              | object        | Конфигурация аудио-вывода (voice, format)                |
| `user`               | string        | Идентификатор конечного пользователя                     |

## Структура сообщений

### Базовый формат

```json theme={null}
{
  "role": "user|assistant|system|developer|tool",
  "content": "Текст сообщения"
}
```

### Мультимодальные сообщения

```json theme={null}
{
  "role": "user",
  "content": [
    {"type": "text", "text": "Что на этом изображении?"},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
  ]
}
```

### Другие типы контента

```json theme={null}
// Аудио вход
{"type": "input_audio", "input_audio": {"data": "base64...", "format": "mp3"}}

// Видео вход
{"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}

// Файл
{"type": "file", "file": {"filename": "doc.pdf", "file_data": "data:application/pdf;base64,..."}}
```

### Системные сообщения с кешированием

```json theme={null}
{
  "role": "system",
  "content": [
    {
      "type": "text",
      "text": "Длинная системная инструкция...",
      "cache_control": {"type": "ephemeral"}
    }
  ]
}
```

## Примеры

<CodeGroup>
  ```bash cURL theme={null}
  curl -X POST "https://polza.ai/api/v1/chat/completions" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/gpt-4o",
      "messages": [{"role": "user", "content": "Привет!"}]
    }'
  ```

  ```python Python theme={null}
  from openai import OpenAI

  client = OpenAI(
      base_url="https://polza.ai/api/v1",
      api_key="YOUR_API_KEY"
  )

  response = client.chat.completions.create(
      model="anthropic/claude-sonnet-4-5-20250929",
      messages=[{"role": "user", "content": "Объясни квантовую механику"}]
  )

  print(response.choices[0].message.content)
  print(f"Стоимость: {response.usage.cost_rub} руб.")
  ```

  ```typescript TypeScript theme={null}
  import OpenAI from 'openai';

  const client = new OpenAI({
      baseURL: 'https://polza.ai/api/v1',
      apiKey: 'YOUR_API_KEY'
  });

  const response = await client.chat.completions.create({
      model: 'openai/gpt-4o',
      messages: [{role: 'user', content: 'Напиши историю'}],
      stream: true
  });

  for await (const chunk of response) {
      process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
  ```
</CodeGroup>

## Ответ

### Успешный ответ (200)

```json theme={null}
{
  "id": "gen_581761234567890123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "openai/gpt-4o",
  "provider": "OpenAI",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Текст ответа"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175,
    "cost_rub": 0.04131306,
    "cost": 0.04131306,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0
    }
  }
}
```

### Streaming (SSE)

При `stream: true` ответ приходит в формате Server-Sent Events:

```
data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"role":"assistant","content":"Привет"}}]}

data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"content":" мир"}}]}

data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30,"cost_rub":0.015,"cost":0.015}}

data: [DONE]
```

## Tool Calling

### Определение функций

```json theme={null}
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Получить текущую погоду",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        },
        "required": ["city"]
      }
    }
  }],
  "tool_choice": "auto"
}
```

### Ответ модели с вызовом функции

```json theme={null}
{
  "tool_calls": [{
    "id": "call_123",
    "function": {"name": "get_weather", "arguments": "{\"city\": \"Москва\"}"}
  }]
}
```

## Response Format

### JSON Schema (структурированный вывод)

```json theme={null}
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "my_schema",
      "schema": {
        "type": "object",
        "properties": {
          "answer": {"type": "string"},
          "confidence": {"type": "number"}
        }
      },
      "strict": true
    }
  }
}
```

Поддерживаемые типы: `text`, `json_object`, `json_schema`, `grammar` (GBNF).

## Reasoning Tokens

Для моделей с рассуждениями (o1, o3, DeepSeek-R1 и другие):

```json theme={null}
{
  "model": "openai/o1-preview",
  "messages": [{"role": "user", "content": "Реши: 2x + 5 = 13"}],
  "reasoning": {
    "effort": "high",
    "max_tokens": 1000
  }
}
```

### Параметры reasoning

| Параметр     | Тип     | Описание                                                |
| ------------ | ------- | ------------------------------------------------------- |
| `effort`     | string  | Уровень усилий: xhigh, high, medium, low, minimal, none |
| `max_tokens` | integer | Максимум токенов на рассуждения                         |
| `summary`    | string  | Детализация: auto, concise, detailed                    |
| `enabled`    | boolean | Включить/выключить рассуждения                          |
| `exclude`    | boolean | Скрыть рассуждения из ответа                            |


## OpenAPI

````yaml POST /v1/chat/completions
openapi: 3.0.0
info:
  title: Polza.ai API
  description: AI агрегатор — унифицированный доступ к сотням AI моделей
  version: '1.0'
  contact: {}
servers:
  - url: https://polza.ai/api
    description: Production
security: []
tags: []
paths:
  /v1/chat/completions:
    post:
      tags:
        - Чат
      summary: Создать chat completion
      operationId: ChatController_createChatCompletion[1]
      parameters: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatCompletionRequestDto'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatCompletionPresenter'
        '400':
          description: Некорректный запрос. Проверьте параметры и тело
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '401':
          description: Ошибка авторизации. Проверьте ключ доступа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '402':
          description: Недостаточно средств или достигнут лимит
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '403':
          description: Ошибка доступа. Проверьте права доступа ключа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '404':
          description: Ресурс не найден
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '408':
          description: Истекло время ожидания ответа. Повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '409':
          description: Конфликт состояния. Перечитайте ресурс и повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '413':
          description: Размер тела запроса превышает допустимый предел
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '429':
          description: Слишком много запросов. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '500':
          description: Ошибка сервера. Обратитесь к поставщику услуг
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '502':
          description: Поставщик услуг вернул некорректный ответ
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '503':
          description: Сервис временно недоступен. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
      security:
        - bearer: []
components:
  schemas:
    ChatCompletionRequestDto:
      type: object
      properties:
        model:
          type: string
          description: >-
            Идентификатор модели. Для Chat Completions API поддерживается
            alias-формат <model>@<key>=<value>&<key>=<value>. Поддерживаемые
            ключи: provider, reasoning_effort, allow_fallbacks. При конфликте
            alias и обычных полей body API возвращает 400. Для некоторых
            провайдеров и моделей допустимые значения reasoning_effort
            отличаются; например, Yandex AI Studio поддерживает только low,
            medium и high.
          example: >-
            openai/gpt-4o@provider=google&reasoning_effort=high&allow_fallbacks=false
        prompt:
          type: string
          description: >-
            Текстовый промпт (альтернатива messages). Если указан, будет
            преобразован в messages с role=user
          example: Напиши стихотворение про кота
        messages:
          description: >-
            Массив сообщений для отправки модели (обязателен если не указан
            prompt)
          example:
            - role: system
              content: Ты полезный ассистент
            - role: user
              content: Привет! Как дела?
          type: array
          items:
            $ref: '#/components/schemas/MessageDto'
        max_tokens:
          type: number
          description: Максимальное количество токенов для генерации
          example: 1000
          minimum: 1
        max_completion_tokens:
          type: number
          description: >-
            Максимальное количество токенов для completion (альтернатива
            max_tokens)
          example: 1000
          minimum: 1
        temperature:
          type: number
          description: >-
            Температура сэмплинга (0-2). Более высокие значения делают вывод
            более случайным
          example: 1
          minimum: 0
          maximum: 2
        top_p:
          type: number
          description: 'Nucleus sampling: вероятностная масса для рассмотрения (0-1)'
          example: 1
          minimum: 0
          maximum: 1
        frequency_penalty:
          type: number
          description: Штраф за частоту использования токенов (-2 до 2)
          example: 0
          minimum: -2
          maximum: 2
        presence_penalty:
          type: number
          description: Штраф за присутствие токенов (-2 до 2)
          example: 0
          minimum: -2
          maximum: 2
        response_format:
          type: object
          description: Формат ответа модели
        provider:
          description: Настройки провайдера для роутинга и фильтрации
          allOf:
            - $ref: '#/components/schemas/ProviderDto'
        tools:
          description: >-
            Определения инструментов: function (исполняет клиент) и серверные
            polza:* (исполняем мы внутри запроса)
          type: array
          items:
            $ref: '#/components/schemas/ToolDefinitionDto'
        max_tool_calls:
          type: number
          description: >-
            Максимум вызовов серверных инструментов за запрос (по умолчанию 10,
            потолок 30; без polza:* игнорируется)
          example: 10
        stop_server_tools_when:
          description: >-
            Условия остановки цикла серверных инструментов; переопределяют
            max_tool_calls
          type: array
          items:
            $ref: '#/components/schemas/StopServerToolsWhenDto'
        stream_options:
          description: Опции стриминга
          allOf:
            - $ref: '#/components/schemas/ChatStreamOptionsDto'
        tool_choice:
          type: object
          description: 'Выбор инструмента: none, auto, required или named function'
          example: auto
        reasoning:
          description: Настройки reasoning для reasoning моделей
          allOf:
            - $ref: '#/components/schemas/ReasoningDto'
        plugins:
          type: array
          description: Плагины для расширения функциональности
        web_search_options:
          description: Настройки встроенного веб-поиска (для моделей с нативной поддержкой)
          allOf:
            - $ref: '#/components/schemas/WebSearchOptionsDto'
        user:
          type: string
          description: >-
            Уникальный идентификатор конечного пользователя для отслеживания и
            предотвращения злоупотреблений
          example: user-123
        stop:
          description: Последовательности, при которых модель прекращает генерацию
          example:
            - |+

          oneOf:
            - type: string
            - type: array
              items:
                type: string
        seed:
          type: number
          description: Seed для детерминированной генерации (best-effort)
          example: 42
        'n':
          type: number
          description: Количество вариантов ответа (1-10)
          example: 1
          minimum: 1
          maximum: 10
        stream:
          type: boolean
          description: Включить потоковую передачу ответа
          example: false
        logprobs:
          type: boolean
          description: Возвращать log probabilities для output токенов
          example: false
        top_logprobs:
          type: number
          description: >-
            Количество наиболее вероятных токенов для возврата (0-20). Требует
            logprobs: true
          example: 5
          minimum: 0
          maximum: 20
        logit_bias:
          type: object
          description: Смещение вероятностей токенов по их ID (-100 до 100)
          example:
            '50256': -100
        parallel_tool_calls:
          type: boolean
          description: Разрешить параллельный вызов нескольких tools
          example: true
        image_config:
          type: object
          description: Настройки обработки изображений
          example:
            quality: high
            size: 512
        media_resolution:
          type: string
          description: >-
            Разрешение обработки медиа для google/gemini-* моделей (Gemini
            media_resolution). Допустимые значения: MEDIA_RESOLUTION_LOW,
            MEDIA_RESOLUTION_MEDIUM, MEDIA_RESOLUTION_HIGH,
            MEDIA_RESOLUTION_UNSPECIFIED. Для остальных моделей игнорируется.
          example: MEDIA_RESOLUTION_LOW
        modalities:
          type: array
          description: Типы вывода модели
          example:
            - text
            - audio
          items:
            type: string
            enum:
              - text
              - image
              - audio
        audio:
          type: object
          description: >-
            Настройки аудио выхода для моделей с поддержкой аудио (gpt-audio и
            др.)
          properties:
            voice:
              type: string
              example: alloy
              description: Голос для генерации аудио
            format:
              type: string
              example: pcm16
              description: Формат аудио
      required:
        - model
        - messages
    ChatCompletionPresenter:
      type: object
      properties:
        id:
          type: string
          description: Уникальный идентификатор генерации
          example: gen_581761234567890123
        object:
          type: string
          description: Тип объекта
          example: chat.completion
        created:
          type: number
          description: Временная метка создания (Unix timestamp)
          example: 1703001234
        model:
          type: string
          description: ID модели, которая сгенерировала ответ
          example: openai/gpt-4o
        choices:
          description: Массив вариантов ответа
          type: array
          items:
            $ref: '#/components/schemas/ChoicePresenter'
        provider:
          type: string
          description: Провайдер обработавший запрос
          example: openai-direct
        system_fingerprint:
          type: string
          description: System fingerprint от провайдера
          example: fp_29330a9688
        usage:
          description: Информация об использовании токенов
          allOf:
            - $ref: '#/components/schemas/UsagePresenter'
        polza:
          type: object
          description: 'Связка server tools: id родителя-«конверта»'
          example:
            parent_generation_id: gen_…
      required:
        - id
        - object
        - created
        - model
        - choices
    ApiErrorPresenter:
      type: object
      properties:
        error:
          description: Информация об ошибке
          allOf:
            - $ref: '#/components/schemas/ApiErrorBodyPresenter'
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
      required:
        - error
    MessageDto:
      type: object
      properties:
        role:
          type: string
          description: Роль отправителя сообщения
          enum:
            - user
            - assistant
            - system
            - developer
            - tool
          example: user
        content:
          type: object
          description: >-
            Содержимое сообщения (строка, массив частей контента или null для
            assistant с tool_calls)
          example: Привет, как дела?
          nullable: true
        name:
          type: string
          description: Имя отправителя (опционально)
          example: Иван
        tool_call_id:
          type: string
          description: ID вызова инструмента (только для role=tool)
          example: call_abc123
        tool_calls:
          description: Массив вызовов инструментов (только для role=assistant)
          type: array
          items:
            $ref: '#/components/schemas/ToolCallDto'
        refusal:
          type: object
          description: >-
            Текст отказа модели от выполнения запроса (только для
            role=assistant)
          example: Я не могу помочь с этим запросом
          nullable: true
        reasoning:
          type: object
          description: Reasoning текст для моделей с reasoning (только для role=assistant)
          example: Для решения этой задачи мне нужно...
          nullable: true
        annotations:
          type: array
          description: >-
            Аннотации из ответа провайдера (для кэширования парсинга PDF и
            других документов)
          items:
            type: object
      required:
        - role
        - content
    ProviderDto:
      type: object
      properties:
        require_parameters:
          type: boolean
          description: Требовать от OpenRouter поддержку всех переданных параметров
          example: true
        allow_fallbacks:
          type: boolean
          description: Разрешить использование резервных провайдеров
          example: true
        order:
          description: Упорядоченный список slug провайдеров для использования
          example:
            - OpenAI
            - Anthropic
          type: array
          items:
            type: string
        only:
          description: Список разрешенных slug провайдеров
          example:
            - OpenAI
            - Google
          type: array
          items:
            type: string
        ignore:
          description: Список игнорируемых slug провайдеров
          example:
            - DeepInfra
          type: array
          items:
            type: string
        sort:
          type: string
          description: Критерий сортировки провайдеров
          enum:
            - price
            - throughput
            - latency
          example: price
        max_price:
          description: Максимальные цены для запроса
          allOf:
            - $ref: '#/components/schemas/ProviderMaxPriceDto'
    ToolDefinitionDto:
      type: object
      properties:
        type:
          type: string
          description: Тип инструмента
          example: function
          enum:
            - function
        function:
          description: Определение функции
          allOf:
            - $ref: '#/components/schemas/ToolFunctionDto'
      required:
        - type
        - function
    StopServerToolsWhenDto:
      type: object
      properties:
        type:
          type: string
          description: Тип условия
          enum:
            - step_count
            - spend_cap
          example: step_count
        value:
          type: number
          description: 'Для step_count: максимум вызовов серверных инструментов'
          example: 5
        value_rub:
          type: number
          description: 'Для spend_cap: потолок расходов на запрос, RUB'
          example: 20
      required:
        - type
    ChatStreamOptionsDto:
      type: object
      properties:
        include_usage:
          type: boolean
          description: Отдавать usage в финальном чанке (совместимость OpenAI)
          example: true
        include_server_tool_events:
          type: boolean
          description: >-
            Отдавать события цикла server tools (tool_call, tool_result,
            step_end) полем `polza` в чанках
          example: false
        hide_intermediate_text:
          type: boolean
          description: >-
            Не проксировать текст промежуточных шагов цикла server tools
            («Сейчас поищу…»); финальный ответ приходит одним куском после
            завершения шага. Только для stream
          example: false
    ReasoningDto:
      type: object
      properties:
        type:
          type: string
          description: >-
            Тип reasoning: adaptive — автовыбор глубины (Claude 4.6+), disabled
            — отключить. Для Claude 4.6+ используйте adaptive вместо
            enabled+max_tokens
          enum:
            - adaptive
            - disabled
          example: adaptive
        effort:
          type: string
          description: >-
            Уровень усилий reasoning модели. Для некоторых провайдеров и моделей
            допустимые значения могут отличаться. Проверяйте документацию
            конкретного провайдера. Например, для Yandex AI Studio
            поддерживаются только low, medium и high.
          enum:
            - max
            - xhigh
            - high
            - medium
            - low
            - minimal
            - none
          example: medium
        effort_level:
          type: string
          description: >-
            Уровень усилий для adaptive thinking (Claude 4.6+). Значение max
            даёт максимальную глубину мышления. Используется вместо effort для
            Claude 4.6+ моделей
          example: max
        summary:
          type: string
          description: Уровень детализации резюме reasoning
          enum:
            - auto
            - concise
            - detailed
            - none
          example: auto
        enabled:
          type: boolean
          description: >-
            Включить/выключить reasoning. По умолчанию определяется из effort
            или max_tokens
          example: true
        max_tokens:
          type: number
          description: Максимальное количество токенов для reasoning (стиль Anthropic)
          example: 2000
        exclude:
          type: boolean
          description: >-
            Скрыть reasoning из ответа (модель будет использовать reasoning, но
            не вернёт его)
          example: false
    WebSearchOptionsDto:
      type: object
      properties:
        search_context_size:
          type: string
          description: Размер контекста поиска для моделей со встроенным веб-поиском
          enum:
            - low
            - medium
            - high
          example: medium
    ChoicePresenter:
      type: object
      properties:
        index:
          type: number
          description: Индекс выбора в массиве choices
          example: 0
        message:
          description: Сообщение от модели
          allOf:
            - $ref: '#/components/schemas/MessagePresenter'
        finish_reason:
          type: string
          description: Причина завершения генерации
          example: stop
          enum:
            - stop
            - length
            - content_filter
            - error
            - tool_calls
          nullable: true
        reasoning_details:
          type: array
          description: Детали reasoning процесса (для reasoning моделей)
        logprobs:
          description: Log probabilities для токенов
          nullable: true
          allOf:
            - $ref: '#/components/schemas/ChatMessageTokenLogprobsPresenter'
      required:
        - index
        - message
        - finish_reason
    UsagePresenter:
      type: object
      properties:
        prompt_tokens:
          type: number
          description: Количество токенов в промпте
          example: 10
        completion_tokens:
          type: number
          description: Количество токенов в ответе
          example: 50
        total_tokens:
          type: number
          description: Общее количество токенов (prompt + completion)
          example: 60
        completion_tokens_details:
          description: Детализация токенов completion
          nullable: true
          allOf:
            - $ref: '#/components/schemas/CompletionTokensDetailsPresenter'
        prompt_tokens_details:
          description: Детализация токенов промпта
          nullable: true
          allOf:
            - $ref: '#/components/schemas/PromptTokensDetailsPresenter'
        server_tool_use:
          description: Использование серверных инструментов (web search)
          nullable: true
          allOf:
            - $ref: '#/components/schemas/ServerToolUsePresenter'
        cost_rub:
          type: object
          description: Стоимость запроса в рублях (списано с баланса клиента)
          example: 0.04131306
          nullable: true
        cost:
          type: object
          description: Стоимость запроса в рублях (alias для cost_rub)
          example: 0.04131306
          nullable: true
        cost_details:
          type: object
          description: Разбивка стоимости цикла server tools, RUB
          example:
            inference_cost_rub: 1.2
            server_tools_cost_rub: 0.4
          nullable: true
        server_tool_use_details:
          type: object
          description: 'Детали цикла server tools: вызовы по инструментам, шаги'
          example:
            web_search_requests: 1
            tool_calls_requested: 2
            tool_calls_executed: 2
            steps: 2
          nullable: true
        plugins:
          type: object
          description: Детализация серверных плагинов
          example:
            masker:
              operations:
                - operation: mask
                  latency_ms: 15
                  cost_rub: 0.001
                - operation: unmask
                  latency_ms: 8
                  cost_rub: 0
              total_cost_rub: 0.001
          nullable: true
        plugin_post_process_error:
          type: boolean
          description: >-
            Ошибка post-process плагинов (ответ возвращён в замаскированном
            виде)
          example: true
      required:
        - prompt_tokens
        - completion_tokens
        - total_tokens
    ApiErrorBodyPresenter:
      type: object
      properties:
        code:
          type: string
          description: Код ошибки
          enum:
            - BAD_REQUEST
            - UNAUTHORIZED
            - api_key_revoked
            - INSUFFICIENT_BALANCE
            - FORBIDDEN
            - NOT_FOUND
            - REQUEST_TIMEOUT
            - CONFLICT
            - PAYLOAD_TOO_LARGE
            - TOO_MANY_REQUESTS
            - BAD_GATEWAY
            - SERVICE_UNAVAILABLE
            - INTERNAL_ERROR
          example: BAD_REQUEST
        message:
          type: string
          description: Описание ошибки
          example: Недопустимое значение параметра
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
        details:
          type: object
          description: Уточняющие поля ошибки. Отдаются только для 4xx
          additionalProperties: true
        metadata:
          description: Метаданные ошибки провайдера
          allOf:
            - $ref: '#/components/schemas/ApiErrorMetadataPresenter'
      required:
        - code
        - message
    ToolCallDto:
      type: object
      properties:
        id:
          type: string
          description: Уникальный идентификатор вызова инструмента
          example: call_abc123xyz
        type:
          type: string
          description: Тип вызова инструмента
          enum:
            - function
          example: function
        function:
          description: Информация о вызываемой функции
          allOf:
            - $ref: '#/components/schemas/ToolCallFunctionDto'
      required:
        - id
        - type
        - function
    ProviderMaxPriceDto:
      type: object
      properties:
        prompt:
          type: number
          description: Максимальная цена за промпт токены (RUB за миллион токенов)
          example: 10
        completion:
          type: number
          description: Максимальная цена за completion токены (RUB за миллион токенов)
          example: 20
        image:
          type: number
          description: Максимальная цена за изображение (RUB за штуку)
          example: 5
        audio:
          type: number
          description: Максимальная цена за аудио (RUB за миллион токенов)
          example: 15
        request:
          type: number
          description: Максимальная цена за запрос (RUB за запрос)
          example: 1
        video_per_second:
          type: number
          description: Максимальная цена за секунду видео (RUB за секунду)
          example: 50
        stt_per_minute:
          type: number
          description: Максимальная цена распознавания речи (RUB за минуту)
          example: 5
        tts_per_million_characters:
          type: number
          description: Максимальная цена синтеза речи (RUB за миллион символов)
          example: 1500
    ToolFunctionDto:
      type: object
      properties:
        name:
          type: string
          description: Название функции
          example: get_weather
        description:
          type: string
          description: Описание функции
          example: Получить текущую погоду для указанного местоположения
        parameters:
          type: object
          description: JSON Schema параметров функции
          example:
            type: object
            properties:
              location:
                type: string
                description: Название города
              unit:
                type: string
                enum:
                  - celsius
                  - fahrenheit
            required:
              - location
        strict:
          type: boolean
          description: Строгое соответствие схеме
          example: false
      required:
        - name
    MessagePresenter:
      type: object
      properties:
        role:
          type: string
          description: Роль отправителя сообщения
          example: assistant
        content:
          type: object
          description: Содержимое сообщения
          example: Привет! Я хорошо, спасибо что спросили. Чем могу помочь?
          nullable: true
        name:
          type: object
          description: Имя отправителя
          example: Ассистент
          nullable: true
        tool_calls:
          description: Вызовы инструментов (tool calls)
          type: array
          items:
            $ref: '#/components/schemas/ToolCallPresenter'
        refusal:
          type: object
          description: Отказ модели от выполнения запроса
          example: null
          nullable: true
        reasoning:
          type: object
          description: Reasoning текст (для reasoning моделей)
          example: null
          nullable: true
        audio:
          type: object
          description: Аудио данные (для моделей с audio output)
          properties:
            id:
              type: string
              description: ID аудио
            data:
              type: string
              description: Base64-encoded аудио данные
            transcript:
              type: string
              description: Текстовая расшифровка
            expires_at:
              type: number
              description: Unix timestamp истечения
        annotations:
          type: array
          description: Аннотации (ссылки на источники от web search)
          items:
            type: object
      required:
        - role
        - content
    ChatMessageTokenLogprobsPresenter:
      type: object
      properties:
        content:
          description: Log probabilities для контента
          nullable: true
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobPresenter'
        refusal:
          description: Log probabilities для refusal
          nullable: true
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobPresenter'
      required:
        - content
        - refusal
    CompletionTokensDetailsPresenter:
      type: object
      properties:
        reasoning_tokens:
          type: object
          description: Токены reasoning (для reasoning моделей)
          example: 100
          nullable: true
        audio_tokens:
          type: object
          description: Аудио токены в ответе
          example: 0
          nullable: true
        image_tokens:
          type: object
          description: Токены изображений в ответе
          example: 0
          nullable: true
        accepted_prediction_tokens:
          type: object
          description: Принятые токены предсказаний
          example: 0
          nullable: true
        rejected_prediction_tokens:
          type: object
          description: Отклоненные токены предсказаний
          example: 0
          nullable: true
    PromptTokensDetailsPresenter:
      type: object
      properties:
        cached_tokens:
          type: number
          description: Кэшированные токены
          example: 0
        cache_write_tokens:
          type: number
          description: Токены, записанные в prompt cache
          example: 0
        audio_tokens:
          type: number
          description: Аудио токены в промпте
          example: 0
        video_tokens:
          type: number
          description: Видео токены в промпте
          example: 0
    ServerToolUsePresenter:
      type: object
      properties:
        web_search_requests:
          type: number
          description: Количество вызовов веб-поиска
          example: 1
    ApiErrorMetadataPresenter:
      type: object
      properties:
        reason:
          type: string
          description: 'Машинная причина отказа: по ней можно ветвиться, не разбирая текст'
          example: noProvidersForModel
        raw:
          type: string
          description: Исходный текст ответа провайдера
          example: The parameter `duration` specified in the request is not valid
        provider_name:
          type: string
          description: Провайдер, вернувший ошибку
          example: openrouter
        attempts:
          description: Кого перебрали, прежде чем отказать
          type: array
          items:
            $ref: '#/components/schemas/ApiErrorAttemptPresenter'
    ToolCallFunctionDto:
      type: object
      properties:
        name:
          type: string
          description: Имя вызываемой функции
          example: get_weather
        arguments:
          type: string
          description: JSON-строка с аргументами функции
          example: '{"location": "Moscow", "unit": "celsius"}'
      required:
        - name
        - arguments
    ToolCallPresenter:
      type: object
      properties:
        id:
          type: string
          description: ID вызова функции
          example: call_abc123
        type:
          type: string
          description: Тип вызова
          example: function
        function:
          description: Информация о функции
          allOf:
            - $ref: '#/components/schemas/ToolCallFunctionPresenter'
      required:
        - id
        - type
        - function
    ChatMessageTokenLogprobPresenter:
      type: object
      properties:
        token:
          type: string
          description: Токен
          example: hello
        logprob:
          type: number
          description: Log probability токена
          example: -0.5
        bytes:
          type: object
          description: Байты токена
          example:
            - 104
            - 101
            - 108
            - 108
            - 111
          nullable: true
        top_logprobs:
          description: Топ наиболее вероятных токенов с их вероятностями
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobTopItemPresenter'
      required:
        - token
        - logprob
        - bytes
        - top_logprobs
    ApiErrorAttemptPresenter:
      type: object
      properties:
        provider:
          type: string
          description: Провайдер, к которому обращались
          example: OpenRouter
        reason:
          type: string
          description: Машинная причина отказа провайдера
          example: RATE_LIMIT
      required:
        - provider
        - reason
    ToolCallFunctionPresenter:
      type: object
      properties:
        name:
          type: string
          description: Название функции
          example: get_weather
        arguments:
          type: string
          description: Аргументы функции в JSON формате
          example: '{"location": "Moscow"}'
      required:
        - name
        - arguments
    ChatMessageTokenLogprobTopItemPresenter:
      type: object
      properties:
        token:
          type: string
          description: Токен
          example: hello
        logprob:
          type: number
          description: Log probability токена
          example: -0.5
        bytes:
          type: object
          description: Байты токена
          example:
            - 104
            - 101
            - 108
            - 108
            - 111
          nullable: true
      required:
        - token
        - logprob
        - bytes
  securitySchemes:
    bearer:
      scheme: bearer
      bearerFormat: API Key
      type: http
      description: >-
        API ключ передаётся в заголовке: Authorization: Bearer
        <POLZA_AI_API_KEY>

````

> ## Documentation Index
> Fetch the complete documentation index at: https://polza.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# POST Chat Completions

> Основной эндпоинт для генерации текста и диалогов

Поддерживает текстовые диалоги, мультимодальные запросы (текст + изображения + аудио + видео + файлы), вызов функций и потоковую передачу.

## Возможности

* **Агрегация провайдеров** — автоматический выбор оптимального провайдера
* **Биллинг в рублях** — точный учет стоимости
* **Reasoning Tokens** — поддержка моделей с рассуждениями
* **Streaming** — потоковая передача через SSE
* **Tool Calling** — вызов внешних функций
* **Мультимодальность** — обработка текста, изображений, аудио, видео и файлов

## Параметры запроса

### Обязательные

| Параметр | Тип    | Описание                                                  |
| -------- | ------ | --------------------------------------------------------- |
| `model`  | string | ID модели из [списка моделей](/docs/api-reference/models/list) |

### Контент

| Параметр   | Тип    | Описание                                         |
| ---------- | ------ | ------------------------------------------------ |
| `messages` | array  | Массив сообщений диалога (рекомендуется)         |
| `prompt`   | string | Простой текстовый промпт (альтернатива messages) |

### Параметры генерации

| Параметр                | Тип           | По умолчанию | Описание                                        |
| ----------------------- | ------------- | ------------ | ----------------------------------------------- |
| `max_tokens`            | integer       | Без лимита   | Максимум токенов в ответе                       |
| `max_completion_tokens` | integer       | Без лимита   | Альтернатива max\_tokens                        |
| `temperature`           | float (0-2)   | 1.0          | Температура (0=детерминированный, 2=креативный) |
| `top_p`                 | float (0-1)   | 1.0          | Nucleus sampling                                |
| `top_k`                 | integer       | —            | Top-K sampling                                  |
| `frequency_penalty`     | float (-2..2) | 0            | Штраф за повторение слов                        |
| `presence_penalty`      | float (-2..2) | 0            | Штраф за повторение токенов                     |
| `stop`                  | string/array  | —            | Стоп-последовательности                         |
| `seed`                  | integer       | —            | Seed для воспроизводимости                      |

### Специальные возможности

| Параметр             | Тип           | Описание                                                 |
| -------------------- | ------------- | -------------------------------------------------------- |
| `stream`             | boolean       | Включить streaming (SSE)                                 |
| `reasoning`          | object        | Настройки reasoning tokens                               |
| `tools`              | array         | Доступные функции для вызова                             |
| `tool_choice`        | string/object | Выбор инструмента: "none", "auto", "required"            |
| `response_format`    | object        | Формат ответа: text, json\_object, json\_schema, grammar |
| `web_search_options` | object        | Встроенный веб-поиск                                     |
| `provider`           | object        | Конфигурация роутинга по провайдерам                     |
| `plugins`            | array         | Подключение плагинов                                     |
| `modalities`         | array         | Выходные модальности: "text", "image", "audio"           |
| `audio`              | object        | Конфигурация аудио-вывода (voice, format)                |
| `user`               | string        | Идентификатор конечного пользователя                     |

## Структура сообщений

### Базовый формат

```json theme={null}
{
  "role": "user|assistant|system|developer|tool",
  "content": "Текст сообщения"
}
```

### Мультимодальные сообщения

```json theme={null}
{
  "role": "user",
  "content": [
    {"type": "text", "text": "Что на этом изображении?"},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
  ]
}
```

### Другие типы контента

```json theme={null}
// Аудио вход
{"type": "input_audio", "input_audio": {"data": "base64...", "format": "mp3"}}

// Видео вход
{"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}

// Файл
{"type": "file", "file": {"filename": "doc.pdf", "file_data": "data:application/pdf;base64,..."}}
```

### Системные сообщения с кешированием

```json theme={null}
{
  "role": "system",
  "content": [
    {
      "type": "text",
      "text": "Длинная системная инструкция...",
      "cache_control": {"type": "ephemeral"}
    }
  ]
}
```

## Примеры

<CodeGroup>
  ```bash cURL theme={null}
  curl -X POST "https://polza.ai/api/v1/chat/completions" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/gpt-4o",
      "messages": [{"role": "user", "content": "Привет!"}]
    }'
  ```

  ```python Python theme={null}
  from openai import OpenAI

  client = OpenAI(
      base_url="https://polza.ai/api/v1",
      api_key="YOUR_API_KEY"
  )

  response = client.chat.completions.create(
      model="anthropic/claude-sonnet-4-5-20250929",
      messages=[{"role": "user", "content": "Объясни квантовую механику"}]
  )

  print(response.choices[0].message.content)
  print(f"Стоимость: {response.usage.cost_rub} руб.")
  ```

  ```typescript TypeScript theme={null}
  import OpenAI from 'openai';

  const client = new OpenAI({
      baseURL: 'https://polza.ai/api/v1',
      apiKey: 'YOUR_API_KEY'
  });

  const response = await client.chat.completions.create({
      model: 'openai/gpt-4o',
      messages: [{role: 'user', content: 'Напиши историю'}],
      stream: true
  });

  for await (const chunk of response) {
      process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
  ```
</CodeGroup>

## Ответ

### Успешный ответ (200)

```json theme={null}
{
  "id": "gen_581761234567890123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "openai/gpt-4o",
  "provider": "OpenAI",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Текст ответа"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175,
    "cost_rub": 0.04131306,
    "cost": 0.04131306,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0
    }
  }
}
```

### Streaming (SSE)

При `stream: true` ответ приходит в формате Server-Sent Events:

```
data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"role":"assistant","content":"Привет"}}]}

data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[{"index":0,"delta":{"content":" мир"}}]}

data: {"id":"gen_123","object":"chat.completion.chunk","created":1703001234,"model":"openai/gpt-4o","choices":[],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30,"cost_rub":0.015,"cost":0.015}}

data: [DONE]
```

## Tool Calling

### Определение функций

```json theme={null}
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Получить текущую погоду",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        },
        "required": ["city"]
      }
    }
  }],
  "tool_choice": "auto"
}
```

### Ответ модели с вызовом функции

```json theme={null}
{
  "tool_calls": [{
    "id": "call_123",
    "function": {"name": "get_weather", "arguments": "{\"city\": \"Москва\"}"}
  }]
}
```

## Response Format

### JSON Schema (структурированный вывод)

```json theme={null}
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "my_schema",
      "schema": {
        "type": "object",
        "properties": {
          "answer": {"type": "string"},
          "confidence": {"type": "number"}
        }
      },
      "strict": true
    }
  }
}
```

Поддерживаемые типы: `text`, `json_object`, `json_schema`, `grammar` (GBNF).

## Reasoning Tokens

Для моделей с рассуждениями (o1, o3, DeepSeek-R1 и другие):

```json theme={null}
{
  "model": "openai/o1-preview",
  "messages": [{"role": "user", "content": "Реши: 2x + 5 = 13"}],
  "reasoning": {
    "effort": "high",
    "max_tokens": 1000
  }
}
```

### Параметры reasoning

| Параметр     | Тип     | Описание                                                |
| ------------ | ------- | ------------------------------------------------------- |
| `effort`     | string  | Уровень усилий: xhigh, high, medium, low, minimal, none |
| `max_tokens` | integer | Максимум токенов на рассуждения                         |
| `summary`    | string  | Детализация: auto, concise, detailed                    |
| `enabled`    | boolean | Включить/выключить рассуждения                          |
| `exclude`    | boolean | Скрыть рассуждения из ответа                            |


## OpenAPI

````yaml POST /v1/chat/completions
openapi: 3.0.0
info:
  title: Polza.ai API
  description: AI агрегатор — унифицированный доступ к сотням AI моделей
  version: '1.0'
  contact: {}
servers:
  - url: https://polza.ai/api
    description: Production
security: []
tags: []
paths:
  /v1/chat/completions:
    post:
      tags:
        - Чат
      summary: Создать chat completion
      operationId: ChatController_createChatCompletion[1]
      parameters: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ChatCompletionRequestDto'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ChatCompletionPresenter'
        '400':
          description: Некорректный запрос. Проверьте параметры и тело
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '401':
          description: Ошибка авторизации. Проверьте ключ доступа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '402':
          description: Недостаточно средств или достигнут лимит
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '403':
          description: Ошибка доступа. Проверьте права доступа ключа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '404':
          description: Ресурс не найден
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '408':
          description: Истекло время ожидания ответа. Повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '409':
          description: Конфликт состояния. Перечитайте ресурс и повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '413':
          description: Размер тела запроса превышает допустимый предел
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '429':
          description: Слишком много запросов. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '500':
          description: Ошибка сервера. Обратитесь к поставщику услуг
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '502':
          description: Поставщик услуг вернул некорректный ответ
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '503':
          description: Сервис временно недоступен. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
      security:
        - bearer: []
components:
  schemas:
    ChatCompletionRequestDto:
      type: object
      properties:
        model:
          type: string
          description: >-
            Идентификатор модели. Для Chat Completions API поддерживается
            alias-формат <model>@<key>=<value>&<key>=<value>. Поддерживаемые
            ключи: provider, reasoning_effort, allow_fallbacks. При конфликте
            alias и обычных полей body API возвращает 400. Для некоторых
            провайдеров и моделей допустимые значения reasoning_effort
            отличаются; например, Yandex AI Studio поддерживает только low,
            medium и high.
          example: >-
            openai/gpt-4o@provider=google&reasoning_effort=high&allow_fallbacks=false
        prompt:
          type: string
          description: >-
            Текстовый промпт (альтернатива messages). Если указан, будет
            преобразован в messages с role=user
          example: Напиши стихотворение про кота
        messages:
          description: >-
            Массив сообщений для отправки модели (обязателен если не указан
            prompt)
          example:
            - role: system
              content: Ты полезный ассистент
            - role: user
              content: Привет! Как дела?
          type: array
          items:
            $ref: '#/components/schemas/MessageDto'
        max_tokens:
          type: number
          description: Максимальное количество токенов для генерации
          example: 1000
          minimum: 1
        max_completion_tokens:
          type: number
          description: >-
            Максимальное количество токенов для completion (альтернатива
            max_tokens)
          example: 1000
          minimum: 1
        temperature:
          type: number
          description: >-
            Температура сэмплинга (0-2). Более высокие значения делают вывод
            более случайным
          example: 1
          minimum: 0
          maximum: 2
        top_p:
          type: number
          description: 'Nucleus sampling: вероятностная масса для рассмотрения (0-1)'
          example: 1
          minimum: 0
          maximum: 1
        frequency_penalty:
          type: number
          description: Штраф за частоту использования токенов (-2 до 2)
          example: 0
          minimum: -2
          maximum: 2
        presence_penalty:
          type: number
          description: Штраф за присутствие токенов (-2 до 2)
          example: 0
          minimum: -2
          maximum: 2
        response_format:
          type: object
          description: Формат ответа модели
        provider:
          description: Настройки провайдера для роутинга и фильтрации
          allOf:
            - $ref: '#/components/schemas/ProviderDto'
        tools:
          description: >-
            Определения инструментов: function (исполняет клиент) и серверные
            polza:* (исполняем мы внутри запроса)
          type: array
          items:
            $ref: '#/components/schemas/ToolDefinitionDto'
        max_tool_calls:
          type: number
          description: >-
            Максимум вызовов серверных инструментов за запрос (по умолчанию 10,
            потолок 30; без polza:* игнорируется)
          example: 10
        stop_server_tools_when:
          description: >-
            Условия остановки цикла серверных инструментов; переопределяют
            max_tool_calls
          type: array
          items:
            $ref: '#/components/schemas/StopServerToolsWhenDto'
        stream_options:
          description: Опции стриминга
          allOf:
            - $ref: '#/components/schemas/ChatStreamOptionsDto'
        tool_choice:
          type: object
          description: 'Выбор инструмента: none, auto, required или named function'
          example: auto
        reasoning:
          description: Настройки reasoning для reasoning моделей
          allOf:
            - $ref: '#/components/schemas/ReasoningDto'
        plugins:
          type: array
          description: Плагины для расширения функциональности
        web_search_options:
          description: Настройки встроенного веб-поиска (для моделей с нативной поддержкой)
          allOf:
            - $ref: '#/components/schemas/WebSearchOptionsDto'
        user:
          type: string
          description: >-
            Уникальный идентификатор конечного пользователя для отслеживания и
            предотвращения злоупотреблений
          example: user-123
        stop:
          description: Последовательности, при которых модель прекращает генерацию
          example:
            - |+

          oneOf:
            - type: string
            - type: array
              items:
                type: string
        seed:
          type: number
          description: Seed для детерминированной генерации (best-effort)
          example: 42
        'n':
          type: number
          description: Количество вариантов ответа (1-10)
          example: 1
          minimum: 1
          maximum: 10
        stream:
          type: boolean
          description: Включить потоковую передачу ответа
          example: false
        logprobs:
          type: boolean
          description: Возвращать log probabilities для output токенов
          example: false
        top_logprobs:
          type: number
          description: >-
            Количество наиболее вероятных токенов для возврата (0-20). Требует
            logprobs: true
          example: 5
          minimum: 0
          maximum: 20
        logit_bias:
          type: object
          description: Смещение вероятностей токенов по их ID (-100 до 100)
          example:
            '50256': -100
        parallel_tool_calls:
          type: boolean
          description: Разрешить параллельный вызов нескольких tools
          example: true
        image_config:
          type: object
          description: Настройки обработки изображений
          example:
            quality: high
            size: 512
        media_resolution:
          type: string
          description: >-
            Разрешение обработки медиа для google/gemini-* моделей (Gemini
            media_resolution). Допустимые значения: MEDIA_RESOLUTION_LOW,
            MEDIA_RESOLUTION_MEDIUM, MEDIA_RESOLUTION_HIGH,
            MEDIA_RESOLUTION_UNSPECIFIED. Для остальных моделей игнорируется.
          example: MEDIA_RESOLUTION_LOW
        modalities:
          type: array
          description: Типы вывода модели
          example:
            - text
            - audio
          items:
            type: string
            enum:
              - text
              - image
              - audio
        audio:
          type: object
          description: >-
            Настройки аудио выхода для моделей с поддержкой аудио (gpt-audio и
            др.)
          properties:
            voice:
              type: string
              example: alloy
              description: Голос для генерации аудио
            format:
              type: string
              example: pcm16
              description: Формат аудио
      required:
        - model
        - messages
    ChatCompletionPresenter:
      type: object
      properties:
        id:
          type: string
          description: Уникальный идентификатор генерации
          example: gen_581761234567890123
        object:
          type: string
          description: Тип объекта
          example: chat.completion
        created:
          type: number
          description: Временная метка создания (Unix timestamp)
          example: 1703001234
        model:
          type: string
          description: ID модели, которая сгенерировала ответ
          example: openai/gpt-4o
        choices:
          description: Массив вариантов ответа
          type: array
          items:
            $ref: '#/components/schemas/ChoicePresenter'
        provider:
          type: string
          description: Провайдер обработавший запрос
          example: openai-direct
        system_fingerprint:
          type: string
          description: System fingerprint от провайдера
          example: fp_29330a9688
        usage:
          description: Информация об использовании токенов
          allOf:
            - $ref: '#/components/schemas/UsagePresenter'
        polza:
          type: object
          description: 'Связка server tools: id родителя-«конверта»'
          example:
            parent_generation_id: gen_…
      required:
        - id
        - object
        - created
        - model
        - choices
    ApiErrorPresenter:
      type: object
      properties:
        error:
          description: Информация об ошибке
          allOf:
            - $ref: '#/components/schemas/ApiErrorBodyPresenter'
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
      required:
        - error
    MessageDto:
      type: object
      properties:
        role:
          type: string
          description: Роль отправителя сообщения
          enum:
            - user
            - assistant
            - system
            - developer
            - tool
          example: user
        content:
          type: object
          description: >-
            Содержимое сообщения (строка, массив частей контента или null для
            assistant с tool_calls)
          example: Привет, как дела?
          nullable: true
        name:
          type: string
          description: Имя отправителя (опционально)
          example: Иван
        tool_call_id:
          type: string
          description: ID вызова инструмента (только для role=tool)
          example: call_abc123
        tool_calls:
          description: Массив вызовов инструментов (только для role=assistant)
          type: array
          items:
            $ref: '#/components/schemas/ToolCallDto'
        refusal:
          type: object
          description: >-
            Текст отказа модели от выполнения запроса (только для
            role=assistant)
          example: Я не могу помочь с этим запросом
          nullable: true
        reasoning:
          type: object
          description: Reasoning текст для моделей с reasoning (только для role=assistant)
          example: Для решения этой задачи мне нужно...
          nullable: true
        annotations:
          type: array
          description: >-
            Аннотации из ответа провайдера (для кэширования парсинга PDF и
            других документов)
          items:
            type: object
      required:
        - role
        - content
    ProviderDto:
      type: object
      properties:
        require_parameters:
          type: boolean
          description: Требовать от OpenRouter поддержку всех переданных параметров
          example: true
        allow_fallbacks:
          type: boolean
          description: Разрешить использование резервных провайдеров
          example: true
        order:
          description: Упорядоченный список slug провайдеров для использования
          example:
            - OpenAI
            - Anthropic
          type: array
          items:
            type: string
        only:
          description: Список разрешенных slug провайдеров
          example:
            - OpenAI
            - Google
          type: array
          items:
            type: string
        ignore:
          description: Список игнорируемых slug провайдеров
          example:
            - DeepInfra
          type: array
          items:
            type: string
        sort:
          type: string
          description: Критерий сортировки провайдеров
          enum:
            - price
            - throughput
            - latency
          example: price
        max_price:
          description: Максимальные цены для запроса
          allOf:
            - $ref: '#/components/schemas/ProviderMaxPriceDto'
    ToolDefinitionDto:
      type: object
      properties:
        type:
          type: string
          description: Тип инструмента
          example: function
          enum:
            - function
        function:
          description: Определение функции
          allOf:
            - $ref: '#/components/schemas/ToolFunctionDto'
      required:
        - type
        - function
    StopServerToolsWhenDto:
      type: object
      properties:
        type:
          type: string
          description: Тип условия
          enum:
            - step_count
            - spend_cap
          example: step_count
        value:
          type: number
          description: 'Для step_count: максимум вызовов серверных инструментов'
          example: 5
        value_rub:
          type: number
          description: 'Для spend_cap: потолок расходов на запрос, RUB'
          example: 20
      required:
        - type
    ChatStreamOptionsDto:
      type: object
      properties:
        include_usage:
          type: boolean
          description: Отдавать usage в финальном чанке (совместимость OpenAI)
          example: true
        include_server_tool_events:
          type: boolean
          description: >-
            Отдавать события цикла server tools (tool_call, tool_result,
            step_end) полем `polza` в чанках
          example: false
        hide_intermediate_text:
          type: boolean
          description: >-
            Не проксировать текст промежуточных шагов цикла server tools
            («Сейчас поищу…»); финальный ответ приходит одним куском после
            завершения шага. Только для stream
          example: false
    ReasoningDto:
      type: object
      properties:
        type:
          type: string
          description: >-
            Тип reasoning: adaptive — автовыбор глубины (Claude 4.6+), disabled
            — отключить. Для Claude 4.6+ используйте adaptive вместо
            enabled+max_tokens
          enum:
            - adaptive
            - disabled
          example: adaptive
        effort:
          type: string
          description: >-
            Уровень усилий reasoning модели. Для некоторых провайдеров и моделей
            допустимые значения могут отличаться. Проверяйте документацию
            конкретного провайдера. Например, для Yandex AI Studio
            поддерживаются только low, medium и high.
          enum:
            - max
            - xhigh
            - high
            - medium
            - low
            - minimal
            - none
          example: medium
        effort_level:
          type: string
          description: >-
            Уровень усилий для adaptive thinking (Claude 4.6+). Значение max
            даёт максимальную глубину мышления. Используется вместо effort для
            Claude 4.6+ моделей
          example: max
        summary:
          type: string
          description: Уровень детализации резюме reasoning
          enum:
            - auto
            - concise
            - detailed
            - none
          example: auto
        enabled:
          type: boolean
          description: >-
            Включить/выключить reasoning. По умолчанию определяется из effort
            или max_tokens
          example: true
        max_tokens:
          type: number
          description: Максимальное количество токенов для reasoning (стиль Anthropic)
          example: 2000
        exclude:
          type: boolean
          description: >-
            Скрыть reasoning из ответа (модель будет использовать reasoning, но
            не вернёт его)
          example: false
    WebSearchOptionsDto:
      type: object
      properties:
        search_context_size:
          type: string
          description: Размер контекста поиска для моделей со встроенным веб-поиском
          enum:
            - low
            - medium
            - high
          example: medium
    ChoicePresenter:
      type: object
      properties:
        index:
          type: number
          description: Индекс выбора в массиве choices
          example: 0
        message:
          description: Сообщение от модели
          allOf:
            - $ref: '#/components/schemas/MessagePresenter'
        finish_reason:
          type: string
          description: Причина завершения генерации
          example: stop
          enum:
            - stop
            - length
            - content_filter
            - error
            - tool_calls
          nullable: true
        reasoning_details:
          type: array
          description: Детали reasoning процесса (для reasoning моделей)
        logprobs:
          description: Log probabilities для токенов
          nullable: true
          allOf:
            - $ref: '#/components/schemas/ChatMessageTokenLogprobsPresenter'
      required:
        - index
        - message
        - finish_reason
    UsagePresenter:
      type: object
      properties:
        prompt_tokens:
          type: number
          description: Количество токенов в промпте
          example: 10
        completion_tokens:
          type: number
          description: Количество токенов в ответе
          example: 50
        total_tokens:
          type: number
          description: Общее количество токенов (prompt + completion)
          example: 60
        completion_tokens_details:
          description: Детализация токенов completion
          nullable: true
          allOf:
            - $ref: '#/components/schemas/CompletionTokensDetailsPresenter'
        prompt_tokens_details:
          description: Детализация токенов промпта
          nullable: true
          allOf:
            - $ref: '#/components/schemas/PromptTokensDetailsPresenter'
        server_tool_use:
          description: Использование серверных инструментов (web search)
          nullable: true
          allOf:
            - $ref: '#/components/schemas/ServerToolUsePresenter'
        cost_rub:
          type: object
          description: Стоимость запроса в рублях (списано с баланса клиента)
          example: 0.04131306
          nullable: true
        cost:
          type: object
          description: Стоимость запроса в рублях (alias для cost_rub)
          example: 0.04131306
          nullable: true
        cost_details:
          type: object
          description: Разбивка стоимости цикла server tools, RUB
          example:
            inference_cost_rub: 1.2
            server_tools_cost_rub: 0.4
          nullable: true
        server_tool_use_details:
          type: object
          description: 'Детали цикла server tools: вызовы по инструментам, шаги'
          example:
            web_search_requests: 1
            tool_calls_requested: 2
            tool_calls_executed: 2
            steps: 2
          nullable: true
        plugins:
          type: object
          description: Детализация серверных плагинов
          example:
            masker:
              operations:
                - operation: mask
                  latency_ms: 15
                  cost_rub: 0.001
                - operation: unmask
                  latency_ms: 8
                  cost_rub: 0
              total_cost_rub: 0.001
          nullable: true
        plugin_post_process_error:
          type: boolean
          description: >-
            Ошибка post-process плагинов (ответ возвращён в замаскированном
            виде)
          example: true
      required:
        - prompt_tokens
        - completion_tokens
        - total_tokens
    ApiErrorBodyPresenter:
      type: object
      properties:
        code:
          type: string
          description: Код ошибки
          enum:
            - BAD_REQUEST
            - UNAUTHORIZED
            - api_key_revoked
            - INSUFFICIENT_BALANCE
            - FORBIDDEN
            - NOT_FOUND
            - REQUEST_TIMEOUT
            - CONFLICT
            - PAYLOAD_TOO_LARGE
            - TOO_MANY_REQUESTS
            - BAD_GATEWAY
            - SERVICE_UNAVAILABLE
            - INTERNAL_ERROR
          example: BAD_REQUEST
        message:
          type: string
          description: Описание ошибки
          example: Недопустимое значение параметра
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
        details:
          type: object
          description: Уточняющие поля ошибки. Отдаются только для 4xx
          additionalProperties: true
        metadata:
          description: Метаданные ошибки провайдера
          allOf:
            - $ref: '#/components/schemas/ApiErrorMetadataPresenter'
      required:
        - code
        - message
    ToolCallDto:
      type: object
      properties:
        id:
          type: string
          description: Уникальный идентификатор вызова инструмента
          example: call_abc123xyz
        type:
          type: string
          description: Тип вызова инструмента
          enum:
            - function
          example: function
        function:
          description: Информация о вызываемой функции
          allOf:
            - $ref: '#/components/schemas/ToolCallFunctionDto'
      required:
        - id
        - type
        - function
    ProviderMaxPriceDto:
      type: object
      properties:
        prompt:
          type: number
          description: Максимальная цена за промпт токены (RUB за миллион токенов)
          example: 10
        completion:
          type: number
          description: Максимальная цена за completion токены (RUB за миллион токенов)
          example: 20
        image:
          type: number
          description: Максимальная цена за изображение (RUB за штуку)
          example: 5
        audio:
          type: number
          description: Максимальная цена за аудио (RUB за миллион токенов)
          example: 15
        request:
          type: number
          description: Максимальная цена за запрос (RUB за запрос)
          example: 1
        video_per_second:
          type: number
          description: Максимальная цена за секунду видео (RUB за секунду)
          example: 50
        stt_per_minute:
          type: number
          description: Максимальная цена распознавания речи (RUB за минуту)
          example: 5
        tts_per_million_characters:
          type: number
          description: Максимальная цена синтеза речи (RUB за миллион символов)
          example: 1500
    ToolFunctionDto:
      type: object
      properties:
        name:
          type: string
          description: Название функции
          example: get_weather
        description:
          type: string
          description: Описание функции
          example: Получить текущую погоду для указанного местоположения
        parameters:
          type: object
          description: JSON Schema параметров функции
          example:
            type: object
            properties:
              location:
                type: string
                description: Название города
              unit:
                type: string
                enum:
                  - celsius
                  - fahrenheit
            required:
              - location
        strict:
          type: boolean
          description: Строгое соответствие схеме
          example: false
      required:
        - name
    MessagePresenter:
      type: object
      properties:
        role:
          type: string
          description: Роль отправителя сообщения
          example: assistant
        content:
          type: object
          description: Содержимое сообщения
          example: Привет! Я хорошо, спасибо что спросили. Чем могу помочь?
          nullable: true
        name:
          type: object
          description: Имя отправителя
          example: Ассистент
          nullable: true
        tool_calls:
          description: Вызовы инструментов (tool calls)
          type: array
          items:
            $ref: '#/components/schemas/ToolCallPresenter'
        refusal:
          type: object
          description: Отказ модели от выполнения запроса
          example: null
          nullable: true
        reasoning:
          type: object
          description: Reasoning текст (для reasoning моделей)
          example: null
          nullable: true
        audio:
          type: object
          description: Аудио данные (для моделей с audio output)
          properties:
            id:
              type: string
              description: ID аудио
            data:
              type: string
              description: Base64-encoded аудио данные
            transcript:
              type: string
              description: Текстовая расшифровка
            expires_at:
              type: number
              description: Unix timestamp истечения
        annotations:
          type: array
          description: Аннотации (ссылки на источники от web search)
          items:
            type: object
      required:
        - role
        - content
    ChatMessageTokenLogprobsPresenter:
      type: object
      properties:
        content:
          description: Log probabilities для контента
          nullable: true
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobPresenter'
        refusal:
          description: Log probabilities для refusal
          nullable: true
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobPresenter'
      required:
        - content
        - refusal
    CompletionTokensDetailsPresenter:
      type: object
      properties:
        reasoning_tokens:
          type: object
          description: Токены reasoning (для reasoning моделей)
          example: 100
          nullable: true
        audio_tokens:
          type: object
          description: Аудио токены в ответе
          example: 0
          nullable: true
        image_tokens:
          type: object
          description: Токены изображений в ответе
          example: 0
          nullable: true
        accepted_prediction_tokens:
          type: object
          description: Принятые токены предсказаний
          example: 0
          nullable: true
        rejected_prediction_tokens:
          type: object
          description: Отклоненные токены предсказаний
          example: 0
          nullable: true
    PromptTokensDetailsPresenter:
      type: object
      properties:
        cached_tokens:
          type: number
          description: Кэшированные токены
          example: 0
        cache_write_tokens:
          type: number
          description: Токены, записанные в prompt cache
          example: 0
        audio_tokens:
          type: number
          description: Аудио токены в промпте
          example: 0
        video_tokens:
          type: number
          description: Видео токены в промпте
          example: 0
    ServerToolUsePresenter:
      type: object
      properties:
        web_search_requests:
          type: number
          description: Количество вызовов веб-поиска
          example: 1
    ApiErrorMetadataPresenter:
      type: object
      properties:
        reason:
          type: string
          description: 'Машинная причина отказа: по ней можно ветвиться, не разбирая текст'
          example: noProvidersForModel
        raw:
          type: string
          description: Исходный текст ответа провайдера
          example: The parameter `duration` specified in the request is not valid
        provider_name:
          type: string
          description: Провайдер, вернувший ошибку
          example: openrouter
        attempts:
          description: Кого перебрали, прежде чем отказать
          type: array
          items:
            $ref: '#/components/schemas/ApiErrorAttemptPresenter'
    ToolCallFunctionDto:
      type: object
      properties:
        name:
          type: string
          description: Имя вызываемой функции
          example: get_weather
        arguments:
          type: string
          description: JSON-строка с аргументами функции
          example: '{"location": "Moscow", "unit": "celsius"}'
      required:
        - name
        - arguments
    ToolCallPresenter:
      type: object
      properties:
        id:
          type: string
          description: ID вызова функции
          example: call_abc123
        type:
          type: string
          description: Тип вызова
          example: function
        function:
          description: Информация о функции
          allOf:
            - $ref: '#/components/schemas/ToolCallFunctionPresenter'
      required:
        - id
        - type
        - function
    ChatMessageTokenLogprobPresenter:
      type: object
      properties:
        token:
          type: string
          description: Токен
          example: hello
        logprob:
          type: number
          description: Log probability токена
          example: -0.5
        bytes:
          type: object
          description: Байты токена
          example:
            - 104
            - 101
            - 108
            - 108
            - 111
          nullable: true
        top_logprobs:
          description: Топ наиболее вероятных токенов с их вероятностями
          type: array
          items:
            $ref: '#/components/schemas/ChatMessageTokenLogprobTopItemPresenter'
      required:
        - token
        - logprob
        - bytes
        - top_logprobs
    ApiErrorAttemptPresenter:
      type: object
      properties:
        provider:
          type: string
          description: Провайдер, к которому обращались
          example: OpenRouter
        reason:
          type: string
          description: Машинная причина отказа провайдера
          example: RATE_LIMIT
      required:
        - provider
        - reason
    ToolCallFunctionPresenter:
      type: object
      properties:
        name:
          type: string
          description: Название функции
          example: get_weather
        arguments:
          type: string
          description: Аргументы функции в JSON формате
          example: '{"location": "Moscow"}'
      required:
        - name
        - arguments
    ChatMessageTokenLogprobTopItemPresenter:
      type: object
      properties:
        token:
          type: string
          description: Токен
          example: hello
        logprob:
          type: number
          description: Log probability токена
          example: -0.5
        bytes:
          type: object
          description: Байты токена
          example:
            - 104
            - 101
            - 108
            - 108
            - 111
          nullable: true
      required:
        - token
        - logprob
        - bytes
  securitySchemes:
    bearer:
      scheme: bearer
      bearerFormat: API Key
      type: http
      description: >-
        API ключ передаётся в заголовке: Authorization: Bearer
        <POLZA_AI_API_KEY>

````

> ## Documentation Index
> Fetch the complete documentation index at: https://polza.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# POST Audio Transcriptions

> Транскрибация аудио в текст (Speech-to-Text)

<Info>
  Этот эндпоинт совместим с OpenAI SDK и подходит для быстрой миграции существующего кода.
</Info>

<Warning>
  Распознавание речи обслуживается **только** этим эндпоинтом. [Media API](/docs/api-reference/media/create) отвечает за генерацию изображений, видео и музыки — опрашивать через `/v1/media/{id}` статус транскрипции нельзя, он вернёт ошибку `RESULT_EXPIRED`, даже когда текст готов.
</Warning>

## Доступные модели

| Модель                  | ID                                  | Описание                                                                                                                |
| ----------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Whisper 1               | `openai/whisper-1`                  | Классическая модель OpenAI (по умолчанию). Поддерживает `verbose_json`, `srt`, `vtt`, пословные/посегментные таймстампы |
| Whisper Large V3        | `openai/whisper-large-v3`           | Улучшенная multilingual-модель OpenAI. Форматы: `json`, `text`, `verbose_json`                                          |
| Whisper Large V3 Turbo  | `openai/whisper-large-v3-turbo`     | Ускоренная версия Large V3. Форматы: `json`, `text`, `verbose_json`                                                     |
| GPT-4o Transcribe       | `openai/gpt-4o-transcribe`          | Высокое качество. Форматы: `json`, `text`. Поддерживает `include: ["logprobs"]`                                         |
| GPT-4o Mini Transcribe  | `openai/gpt-4o-mini-transcribe`     | Быстрая/дешёвая. Форматы: `json`, `text`. Поддерживает `include: ["logprobs"]`                                          |
| Google Chirp 3          | `google/chirp-3`                    | STT от Google. Форматы: `json`, `text`                                                                                  |
| Qwen3 ASR Flash         | `qwen/qwen3-asr-flash-2026-02-10`   | Быстрая multilingual-модель от Qwen. Форматы: `json`, `text`                                                            |
| Voxtral Mini Transcribe | `mistralai/voxtral-mini-transcribe` | STT от Mistral AI. Форматы: `json`, `text`                                                                              |
| Parakeet TDT 0.6B v3    | `nvidia/parakeet-tdt-0.6b-v3`       | Лёгкая и быстрая модель от NVIDIA. Форматы: `json`, `text`                                                              |
| ElevenLabs STT          | `elevenlabs/speech-to-text`         | STT от ElevenLabs. Поддерживает диаризацию через `diarized_json`                                                        |

> Тарификация STT — посекундная (`per_second`), по длительности аудио.

### Асинхронные модели

| Модель                      | ID                      | Описание                                            |
| --------------------------- | ----------------------- | --------------------------------------------------- |
| Aiesa Транскрипция          | `aiesa/transcribe`      | Диаризация по спикерам, обычная очередь. 0,12 ₽/мин |
| Aiesa Транскрипция (Молния) | `aiesa/transcribe-fast` | То же, ускоренная обработка. 0,40 ₽/мин             |

Эти модели работают иначе: запрос возвращает не текст, а `id` задачи, результат забирается опросом статуса. Подробности и примеры — в руководстве [Aiesa Транскрипция](/docs/gaidy/aiesa-transcribe). Тарификация — по целым минутам, минимум одна минута.

## Параметры запроса

| Параметр                   | Тип                | Обязательный | Описание                                                                                                                                                                                                                                                                                                   |
| -------------------------- | ------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `file`                     | string             | Да           | Аудиофайл: base64 (`data:audio/mp3;base64,...`) или URL                                                                                                                                                                                                                                                    |
| `model`                    | string             | Нет          | Модель транскрибации (по умолчанию `openai/whisper-1`)                                                                                                                                                                                                                                                     |
| `language`                 | string             | Нет          | ISO-639-1: `auto` (по умолчанию), `ru`, `en`, `de`, `fr`, `es`, `it`, `pt`, `pl`, `uk`, `nl`, `sv`, `da`, `fi`, `cs`, `sk`, `ro`, `bg`, `hr`, `el`, `tr`, `ar`, `hi`, `zh`, `ja`, `ko`, `id`. Модели `aiesa/*` значение `auto` не принимают — для них либо укажите язык явно, либо не передавайте параметр |
| `temperature`              | number             | Нет          | Температура (0–1, по умолчанию 0). В основном для `whisper-1`                                                                                                                                                                                                                                              |
| `response_format`          | enum               | Нет          | `json` (по умолчанию), `text`, `srt`, `verbose_json`, `vtt`, `diarized_json`                                                                                                                                                                                                                               |
| `prompt`                   | string             | Нет          | Контекст транскрипции, до \~2048 символов. **Не** поддерживается для `gpt-4o-transcribe-diarize`                                                                                                                                                                                                           |
| `timestamp_granularities`  | string\[]          | Нет          | `word`, `segment` (можно оба). Только `whisper-1` + `verbose_json`                                                                                                                                                                                                                                         |
| `chunking_strategy`        | `'auto'` \| object | Нет          | Стратегия разбивки. **Обязателен** для `gpt-4o-transcribe-diarize` при аудио > 30 сек                                                                                                                                                                                                                      |
| `include`                  | string\[]          | Нет          | `logprobs`. Только `gpt-4o-transcribe` и `gpt-4o-mini-transcribe`                                                                                                                                                                                                                                          |
| `known_speaker_names`      | string\[]          | Нет          | Имена известных спикеров, до 4. Только для диаризации                                                                                                                                                                                                                                                      |
| `known_speaker_references` | string\[]          | Нет          | Аудио-референсы спикеров (data-URL). Только для диаризации                                                                                                                                                                                                                                                 |
| `stream`                   | boolean            | Нет          | Стриминг ответа. **Не** поддерживается для `whisper-1`                                                                                                                                                                                                                                                     |
| `user`                     | string             | Нет          | Идентификатор конечного пользователя                                                                                                                                                                                                                                                                       |

### Допустимые `response_format` по моделям

* `openai/whisper-1` → `json`, `text`, `srt`, `verbose_json`, `vtt`
* `openai/gpt-4o-transcribe`, `openai/gpt-4o-mini-transcribe` → `json`, `text`
* `elevenlabs/speech-to-text` → стандартный набор + `diarized_json`

### Объект `chunking_strategy` типа `server_vad`

| Поле                  | Тип            | Диапазон | Назначение                          |
| --------------------- | -------------- | -------- | ----------------------------------- |
| `type`                | `'server_vad'` | —        | обязателен                          |
| `prefix_padding_ms`   | number         | ≥ 0      | паддинг перед сегментом, мс         |
| `silence_duration_ms` | number         | ≥ 0      | длительность тишины для разрыва, мс |
| `threshold`           | number         | 0–1      | порог громкости (VAD)               |

Либо строкой: `"chunking_strategy": "auto"`.

## Диаризация (gpt-4o-transcribe-diarize)

Модель `gpt-4o-transcribe-diarize` возвращает разбивку по спикерам. Используйте `response_format: "diarized_json"`.

<Warning>
  При аудио длительностью **более 30 секунд** параметр `chunking_strategy` обязателен. Без него запрос вернёт ошибку 400.
</Warning>

Опционально можно заранее «обучить» диаризатор на конкретные голоса:

* `known_speaker_names` — массив имён, **до 4**. Имена используются как метки спикеров.
* `known_speaker_references` — массив data-URL с короткими аудио-примерами тех же спикеров.

## Поддерживаемые форматы файлов

MP3, WAV, M4A, FLAC, OGG, WebM.

<Note>
  Лимит размера тела — около 15 МБ. На больших файлах возможен 502. Для больших аудио разбивайте файл на части.
</Note>

## Примеры

<CodeGroup>
  ```bash cURL theme={null}
  curl -X POST "https://polza.ai/api/v1/audio/transcriptions" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/whisper-1",
      "file": "BASE64_ENCODED_AUDIO",
      "language": "ru"
    }'
  ```

  ```python Python theme={null}
  import requests
  import base64

  with open('audio.mp3', 'rb') as f:
      audio_base64 = base64.b64encode(f.read()).decode('utf-8')

  response = requests.post(
      'https://polza.ai/api/v1/audio/transcriptions',
      headers={'Authorization': 'Bearer YOUR_API_KEY'},
      json={
          'model': 'openai/whisper-1',
          'file': audio_base64,
          'language': 'ru'
      }
  )

  data = response.json()
  print(data['text'])
  ```

  ```javascript JavaScript theme={null}
  const fs = require('fs');

  const audioFile = fs.readFileSync('audio.mp3');
  const audioBase64 = audioFile.toString('base64');

  const response = await fetch('https://polza.ai/api/v1/audio/transcriptions', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'whisper-1',
      file: audioBase64,
      language: 'ru'
    })
  });

  const data = await response.json();
  console.log(data.text);
  ```
</CodeGroup>

### Пример с диаризацией

```bash theme={null}
curl -X POST "https://polza.ai/api/v1/audio/transcriptions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "file": "BASE64_ENCODED_AUDIO",
    "response_format": "diarized_json",
    "chunking_strategy": "auto",
    "known_speaker_names": ["agent", "client"]
  }'
```

## Ответ (200)

### response\_format: json (по умолчанию)

```json theme={null}
{
  "text": "Привет! Это тестовое сообщение.",
  "language": "ru",
  "duration": 10.5,
  "model": "whisper-1",
  "usage": { "durationSeconds": 10.5, "cost": 0.11, "cost_rub": 0.11 }
}
```

### response\_format: verbose\_json (только whisper-1)

```json theme={null}
{
  "text": "Привет, мир!",
  "language": "ru",
  "duration": 5.5,
  "model": "whisper-1",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 5.5,
      "text": "Привет, мир!",
      "tokens": [1, 2, 3],
      "temperature": 0,
      "avg_logprob": -0.5,
      "compression_ratio": 1.2,
      "no_speech_prob": 0.01
    }
  ],
  "words": [
    { "word": "Привет", "start": 0.0, "end": 0.5 }
  ],
  "usage": { "durationSeconds": 5.5, "cost": 0.06, "cost_rub": 0.06 }
}
```

Поле `words` появляется, только если указан `timestamp_granularities: ["word"]`.

### response\_format: diarized\_json (gpt-4o-transcribe-diarize)

```json theme={null}
{
  "task": "transcribe",
  "duration": 27.4,
  "text": "agent: Привет!\nclient: Здравствуйте!",
  "segments": [
    {
      "id": "seg_001",
      "start": 0.0,
      "end": 4.7,
      "text": "Привет, как дела?",
      "speaker": "agent",
      "type": "transcript.text.segment"
    }
  ],
  "model": "gpt-4o-transcribe-diarize",
  "usage": { "durationSeconds": 27, "cost": 0.27, "cost_rub": 0.27 }
}
```

### response\_format: text / srt / vtt

Поле `text` содержит результат — plain text либо готовые субтитры в формате SRT/VTT. Поля `segments`/`words` отсутствуют.

## Поля ответа

| Поле       | Описание                                                             |
| ---------- | -------------------------------------------------------------------- |
| `text`     | Полный транскрибированный текст (для `diarized_json` — со спикерами) |
| `language` | Определённый язык (ISO-639-1)                                        |
| `duration` | Длительность аудио в секундах                                        |
| `segments` | Сегменты с таймкодами (для `verbose_json` и `diarized_json`)         |
| `words`    | Слова с таймкодами (при `timestamp_granularities: ["word"]`)         |
| `usage`    | Использование: `durationSeconds`, `cost_rub`, `cost`                 |

## Ответ асинхронных моделей (`aiesa/*`)

Асинхронные модели вместо текста возвращают идентификатор задачи:

```json theme={null}
{
  "id": "gen_1234567890123456789",
  "object": "transcription",
  "status": "processing",
  "model": "aiesa/transcribe"
}
```

Результат забирается опросом:

```bash theme={null}
curl "https://polza.ai/api/v1/audio/transcriptions/gen_1234567890123456789" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json theme={null}
{
  "id": "gen_1234567890123456789",
  "object": "transcription",
  "status": "completed",
  "text": "Добрый день, начнём совещание. Да, все на связи.",
  "duration": 15,
  "segments": [
    {
      "speaker": "SPEAKER_01",
      "text": "Добрый день, начнём совещание.",
      "start": 0,
      "end": 7,
      "startTime": "00:00:00",
      "endTime": "00:00:07"
    }
  ]
}
```

| Поле       | Описание                                                                     |
| ---------- | ---------------------------------------------------------------------------- |
| `status`   | `processing`, `completed` или `failed`                                       |
| `text`     | Полная расшифровка (при `completed`)                                         |
| `duration` | Длительность аудио в секундах                                                |
| `segments` | Реплики по спикерам: `speaker`, `text`, `start`/`end`, `startTime`/`endTime` |
| `error`    | Описание ошибки при `status: failed`                                         |

Параметр `response_format` на этих моделях не применяется — диаризация всегда приходит в `segments`. Подробнее: [Aiesa Транскрипция](/docs/gaidy/aiesa-transcribe).


## OpenAPI

````yaml POST /v1/audio/transcriptions
openapi: 3.0.0
info:
  title: Polza.ai API
  description: AI агрегатор — унифицированный доступ к сотням AI моделей
  version: '1.0'
  contact: {}
servers:
  - url: https://polza.ai/api
    description: Production
security: []
tags: []
paths:
  /v1/audio/transcriptions:
    post:
      tags:
        - Аудио
      summary: Транскрибировать аудио в текст (STT)
      operationId: AudioSttController_createTranscription[3]
      parameters: []
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/AudioTranscriptionDto'
          application/json:
            schema:
              $ref: '#/components/schemas/AudioTranscriptionDto'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioTranscriptionPresenter'
        '400':
          description: Некорректный запрос. Проверьте параметры и тело
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '401':
          description: Ошибка авторизации. Проверьте ключ доступа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '402':
          description: Недостаточно средств или достигнут лимит
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '403':
          description: Ошибка доступа. Проверьте права доступа ключа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '404':
          description: Ресурс не найден
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '408':
          description: Истекло время ожидания ответа. Повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '409':
          description: Конфликт состояния. Перечитайте ресурс и повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '413':
          description: Размер тела запроса превышает допустимый предел
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '429':
          description: Слишком много запросов. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '500':
          description: Ошибка сервера. Обратитесь к поставщику услуг
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '502':
          description: Поставщик услуг вернул некорректный ответ
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '503':
          description: Сервис временно недоступен. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
      security:
        - bearer: []
components:
  schemas:
    AudioTranscriptionDto:
      type: object
      properties:
        file:
          type: string
          description: Аудио файл в формате base64 (data:audio/mp3;base64,...) или URL
          example: data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAA...
        model:
          type: string
          description: ID модели для транскрипции
          example: whisper-1
          default: whisper-1
        language:
          type: string
          description: 'Язык аудио в формате ISO-639-1 (например: ru, en, de)'
          example: ru
        prompt:
          type: string
          description: Промпт для улучшения контекста транскрипции
          example: Это разговор об искусственном интеллекте
        response_format:
          type: string
          description: Формат ответа
          enum:
            - json
            - text
            - srt
            - verbose_json
            - vtt
            - diarized_json
          default: json
        temperature:
          type: number
          description: Температура сэмплирования (0-1)
          example: 0
          minimum: 0
          maximum: 1
          default: 0
        timestamp_granularities:
          type: array
          description: Granularity для временных меток (только для verbose_json)
          example:
            - word
            - segment
          items:
            type: string
            enum:
              - word
              - segment
        user:
          type: string
          description: >-
            Уникальный идентификатор конечного пользователя для отслеживания и
            предотвращения злоупотреблений
          example: user-123
        chunking_strategy:
          description: >-
            Chunking strategy для разбивки аудио (обязателен для
            gpt-4o-transcribe-diarize при >30 сек)
          oneOf:
            - type: string
              enum:
                - auto
            - 2c0ba518-f6c2-4bf3-a024-3baed178008a
          example: auto
        include:
          type: array
          description: Дополнительная информация в ответе (logprobs)
          example:
            - logprobs
          items:
            type: string
            enum:
              - logprobs
        known_speaker_names:
          description: Имена известных спикеров (до 4)
          example:
            - agent
            - customer
          type: array
          items:
            type: array
        known_speaker_references:
          description: Аудио референсы для известных спикеров (data URLs)
          type: array
          items:
            type: array
        stream:
          type: boolean
          description: Стриминг ответа (не поддерживается для whisper-1)
          example: false
        provider:
          description: Настройки выбора провайдера. В multipart-форме — JSON-строкой
          allOf:
            - $ref: '#/components/schemas/ProviderDto'
      required:
        - file
    AudioTranscriptionPresenter:
      type: object
      properties:
        text:
          type: string
          description: Транскрибированный текст
          example: Привет! Это тестовое сообщение.
        language:
          type: string
          description: Определенный язык аудио (ISO-639-1)
          example: ru
        duration:
          type: number
          description: Длительность аудио в секундах
          example: 10.5
        segments:
          description: Сегменты с таймстампами (для verbose_json)
          type: array
          items:
            $ref: '#/components/schemas/TranscriptionSegmentPresenter'
        words:
          description: Words с таймстампами (для verbose_json с word granularity)
          type: array
          items:
            $ref: '#/components/schemas/TranscriptionWordPresenter'
        model:
          type: string
          description: ID использованной модели
          example: whisper-1
        usage:
          type: object
          description: Информация об использовании
          example:
            durationSeconds: 10.5
            cost: 0.01
            cost_rub: 0.01
      required:
        - text
    ApiErrorPresenter:
      type: object
      properties:
        error:
          description: Информация об ошибке
          allOf:
            - $ref: '#/components/schemas/ApiErrorBodyPresenter'
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
      required:
        - error
    ProviderDto:
      type: object
      properties:
        require_parameters:
          type: boolean
          description: Требовать от OpenRouter поддержку всех переданных параметров
          example: true
        allow_fallbacks:
          type: boolean
          description: Разрешить использование резервных провайдеров
          example: true
        order:
          description: Упорядоченный список slug провайдеров для использования
          example:
            - OpenAI
            - Anthropic
          type: array
          items:
            type: string
        only:
          description: Список разрешенных slug провайдеров
          example:
            - OpenAI
            - Google
          type: array
          items:
            type: string
        ignore:
          description: Список игнорируемых slug провайдеров
          example:
            - DeepInfra
          type: array
          items:
            type: string
        sort:
          type: string
          description: Критерий сортировки провайдеров
          enum:
            - price
            - throughput
            - latency
          example: price
        max_price:
          description: Максимальные цены для запроса
          allOf:
            - $ref: '#/components/schemas/ProviderMaxPriceDto'
    TranscriptionSegmentPresenter:
      type: object
      properties:
        id:
          type: number
          description: ID сегмента
          example: 0
        seek:
          type: number
          description: Seek position
          example: 0
        start:
          type: number
          description: Время начала (секунды)
          example: 0
        end:
          type: number
          description: Время окончания (секунды)
          example: 5.5
        text:
          type: string
          description: Текст сегмента
          example: Привет, мир!
        tokens:
          description: Token IDs
          example:
            - 1
            - 2
            - 3
          type: array
          items:
            type: number
        temperature:
          type: number
          description: Температура
          example: 0
        avg_logprob:
          type: number
          description: Средняя log probability
          example: -0.5
        compression_ratio:
          type: number
          description: Compression ratio
          example: 1.2
        no_speech_prob:
          type: number
          description: Вероятность отсутствия речи
          example: 0.01
      required:
        - id
        - seek
        - start
        - end
        - text
        - tokens
        - temperature
        - avg_logprob
        - compression_ratio
        - no_speech_prob
    TranscriptionWordPresenter:
      type: object
      properties:
        word:
          type: string
          description: Слово
          example: Привет
        start:
          type: number
          description: Время начала (секунды)
          example: 0
        end:
          type: number
          description: Время окончания (секунды)
          example: 0.5
      required:
        - word
        - start
        - end
    ApiErrorBodyPresenter:
      type: object
      properties:
        code:
          type: string
          description: Код ошибки
          enum:
            - BAD_REQUEST
            - UNAUTHORIZED
            - api_key_revoked
            - INSUFFICIENT_BALANCE
            - FORBIDDEN
            - NOT_FOUND
            - REQUEST_TIMEOUT
            - CONFLICT
            - PAYLOAD_TOO_LARGE
            - TOO_MANY_REQUESTS
            - BAD_GATEWAY
            - SERVICE_UNAVAILABLE
            - INTERNAL_ERROR
          example: BAD_REQUEST
        message:
          type: string
          description: Описание ошибки
          example: Недопустимое значение параметра
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
        details:
          type: object
          description: Уточняющие поля ошибки. Отдаются только для 4xx
          additionalProperties: true
        metadata:
          description: Метаданные ошибки провайдера
          allOf:
            - $ref: '#/components/schemas/ApiErrorMetadataPresenter'
      required:
        - code
        - message
    ProviderMaxPriceDto:
      type: object
      properties:
        prompt:
          type: number
          description: Максимальная цена за промпт токены (RUB за миллион токенов)
          example: 10
        completion:
          type: number
          description: Максимальная цена за completion токены (RUB за миллион токенов)
          example: 20
        image:
          type: number
          description: Максимальная цена за изображение (RUB за штуку)
          example: 5
        audio:
          type: number
          description: Максимальная цена за аудио (RUB за миллион токенов)
          example: 15
        request:
          type: number
          description: Максимальная цена за запрос (RUB за запрос)
          example: 1
        video_per_second:
          type: number
          description: Максимальная цена за секунду видео (RUB за секунду)
          example: 50
        stt_per_minute:
          type: number
          description: Максимальная цена распознавания речи (RUB за минуту)
          example: 5
        tts_per_million_characters:
          type: number
          description: Максимальная цена синтеза речи (RUB за миллион символов)
          example: 1500
    ApiErrorMetadataPresenter:
      type: object
      properties:
        reason:
          type: string
          description: 'Машинная причина отказа: по ней можно ветвиться, не разбирая текст'
          example: noProvidersForModel
        raw:
          type: string
          description: Исходный текст ответа провайдера
          example: The parameter `duration` specified in the request is not valid
        provider_name:
          type: string
          description: Провайдер, вернувший ошибку
          example: openrouter
        attempts:
          description: Кого перебрали, прежде чем отказать
          type: array
          items:
            $ref: '#/components/schemas/ApiErrorAttemptPresenter'
    ApiErrorAttemptPresenter:
      type: object
      properties:
        provider:
          type: string
          description: Провайдер, к которому обращались
          example: OpenRouter
        reason:
          type: string
          description: Машинная причина отказа провайдера
          example: RATE_LIMIT
      required:
        - provider
        - reason
  securitySchemes:
    bearer:
      scheme: bearer
      bearerFormat: API Key
      type: http
      description: >-
        API ключ передаётся в заголовке: Authorization: Bearer
        <POLZA_AI_API_KEY>

````

> ## Documentation Index
> Fetch the complete documentation index at: https://polza.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# POST Audio Speech

> Синтез речи из текста (Text-to-Speech)

<Info>
  Этот эндпоинт совместим с OpenAI SDK и подходит для быстрой миграции существующего кода.
  Для синтеза речи рекомендуется именно dedicated-эндпоинт `/v1/audio/speech`: здесь доступен полный диапазон `speed` (0.25–4.0) и согласованный набор параметров под каждое семейство моделей.
  Те же возможности доступны и через общий [Media API](/docs/api-reference/media/create), но там часть параметров (`speed`, `instructions`, ElevenLabs-only поля) ведёт себя иначе или ограничена.
</Info>

## Доступные модели

| Модель                     | ID                                          | Описание                                                    |
| -------------------------- | ------------------------------------------- | ----------------------------------------------------------- |
| TTS                        | `openai/tts-1`                              | OpenAI стандарт (по умолчанию)                              |
| TTS HD                     | `openai/tts-1-hd`                           | OpenAI HD                                                   |
| GPT-4o Mini TTS            | `openai/gpt-4o-mini-tts`                    | OpenAI, управляемый интонацией, поддерживает `instructions` |
| ElevenLabs Multilingual v2 | `elevenlabs/text-to-speech-multilingual-v2` | ElevenLabs многоязычный                                     |
| ElevenLabs Turbo v2.5      | `elevenlabs/text-to-speech-turbo-2-5`       | ElevenLabs Turbo (единственный с `language_code`)           |

## Разрешение голоса по семействам

Параметр `voice` интерпретируется Polza в зависимости от семейства модели. Передача голоса «не из своего» семейства не приводит к ошибке тихо — **голос приводится к дефолту семейства**:

| Семейство      | Дефолт   | Допустимые значения                                                                                                                                                                    |
| -------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `openai/*`     | `alloy`  | `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`, `verse`                                                                                         |
| `elevenlabs/*` | `Rachel` | `voice_id` из аккаунта ElevenLabs (например `pNInz6obpgDQGcFmaJgB`) **или** имя пресета (`Rachel`, `Aria`, `Roger`, `Sarah`...). Стандартный OpenAI-голос будет отклонён с ошибкой 400 |

> В релизе 1.6.7 на каталоге доступны OpenAI и ElevenLabs. Семейства Gemini TTS / Kokoro / MAI Voice поддержаны на уровне разрешения голоса, но включаются отдельно.

## Параметры запроса

| Параметр          | Тип    | Обязательный | Описание                                                                                                          |
| ----------------- | ------ | ------------ | ----------------------------------------------------------------------------------------------------------------- |
| `model`           | string | Нет          | Модель TTS (по умолчанию `openai/tts-1`)                                                                          |
| `input`           | string | Да           | Текст для озвучки, до 5000 символов                                                                               |
| `voice`           | string | Да           | Имя голоса (см. таблицу выше)                                                                                     |
| `response_format` | enum   | Нет          | `mp3` (по умолчанию), `opus`, `aac`, `flac`, `wav`, `pcm`                                                         |
| `speed`           | number | Нет          | Скорость речи, `0.25`–`4.0` (по умолчанию `1.0`). Только OpenAI-модели                                            |
| `instructions`    | string | Нет          | Голосовые инструкции, до 4096 символов. **Только** `openai/gpt-4o-mini-tts`. **Не** работает у `tts-1`/`tts-1-hd` |
| `stream_format`   | enum   | Нет          | `sse` или `audio`. **Не** поддерживается для `tts-1`/`tts-1-hd`                                                   |
| `user`            | string | Нет          | Идентификатор конечного пользователя                                                                              |

### Параметры ElevenLabs

| Параметр           | Тип          | Описание                                                                                                       |
| ------------------ | ------------ | -------------------------------------------------------------------------------------------------------------- |
| `stability`        | number (0–1) | Стабильность голоса (меньше = экспрессивнее)                                                                   |
| `similarity_boost` | number (0–1) | Схожесть с оригинальным голосом                                                                                |
| `style`            | number (0–1) | Эмоциональность                                                                                                |
| `timestamps`       | boolean      | Посимвольный alignment в ответе (`characters`, `character_start_times_seconds`, `character_end_times_seconds`) |
| `previous_text`    | string       | Текст перед текущим фрагментом (контекст), до 5000 символов                                                    |
| `next_text`        | string       | Текст после текущего фрагмента (контекст), до 5000 символов                                                    |
| `language_code`    | string       | ISO-639-1 (`ru`, `en`...). **Только** `elevenlabs/text-to-speech-turbo-2-5`                                    |

## Примеры

<CodeGroup>
  ```bash cURL theme={null}
  curl -X POST "https://polza.ai/api/v1/audio/speech" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/tts-1",
      "input": "Привет! Это Polza.AI!",
      "voice": "alloy"
    }'
  ```

  ```python Python theme={null}
  import requests

  response = requests.post(
      'https://polza.ai/api/v1/audio/speech',
      headers={'Authorization': 'Bearer YOUR_API_KEY'},
      json={
          'model': 'openai/tts-1',
          'input': 'Привет! Это тестовое сообщение.',
          'voice': 'alloy'
      }
  )

  data = response.json()
  print(f"Аудио: {data['audio']}")
  print(f"Длительность: {data.get('duration')} сек")
  ```

  ```javascript JavaScript theme={null}
  const response = await fetch('https://polza.ai/api/v1/audio/speech', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'openai/tts-1',
      input: 'Hello! This is a test message.',
      voice: 'nova'
    })
  });

  const data = await response.json();
  console.log(data.audio);
  ```
</CodeGroup>

### Пример с ElevenLabs + timestamps

```bash theme={null}
curl -X POST "https://polza.ai/api/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "elevenlabs/text-to-speech-multilingual-v2",
    "input": "Привет, как дела?",
    "voice": "Rachel",
    "timestamps": true
  }'
```

## Ответ (200)

```json theme={null}
{
  "audio": "SUQzBAAAAAAAI1RTU0UAAA...",
  "contentType": "audio/mpeg",
  "model": "openai/tts-1",
  "duration": 3.5,
  "usage": {
    "characters": 25,
    "cost_rub": 0.50,
    "cost": 0.50
  }
}
```

| Поле          | Тип    | Описание                                                                                                        |
| ------------- | ------ | --------------------------------------------------------------------------------------------------------------- |
| `audio`       | string | Аудио в формате **base64-строки** (не бинарный поток) — декодируйте и сохраняйте с расширением по `contentType` |
| `contentType` | string | MIME-тип (например, `audio/mpeg`, `audio/wav`, `audio/ogg`)                                                     |
| `model`       | string | Использованная модель                                                                                           |
| `duration`    | number | Длительность в секундах, если известна                                                                          |
| `usage`       | object | Использование: `characters` (для посимвольных моделей), `cost_rub`, `cost`                                      |
| `alignment`   | object | Посимвольные тайминги (только ElevenLabs при `timestamps: true`)                                                |

> Поле `usage.characters` присутствует для посимвольных моделей (`tts-1`/`tts-1-hd`); для токенных (`gpt-4o-mini-tts`) состав `usage` иной.

### Пример ответа ElevenLabs с alignment

```json theme={null}
{
  "audio": "...",
  "contentType": "audio/mpeg",
  "model": "elevenlabs/text-to-speech-multilingual-v2",
  "alignment": {
    "characters": ["П", "р", "и"],
    "character_start_times_seconds": [0.0, 0.05, 0.11],
    "character_end_times_seconds": [0.05, 0.11, 0.18]
  }
}
```

***

## Генерация звуковых эффектов

Также доступна генерация звуков по текстовому описанию через тот же эндпоинт.

### Параметры

| Параметр           | Тип     | Обязательный | Описание                     |
| ------------------ | ------- | ------------ | ---------------------------- |
| `model`            | string  | Да           | Модель генерации звуков      |
| `input`            | string  | Да           | Описание звука на английском |
| `duration_seconds` | number  | Нет          | Длительность (0.5-10 сек)    |
| `loop`             | boolean | Нет          | Зацикленность                |
| `output_format`    | string  | Нет          | Формат аудио                 |
| `prompt_influence` | number  | Нет          | Влияние промпта              |

### Форматы вывода

* `mp3_22050_32` — MP3 22050Hz 32kbps
* `mp3_44100_32` — MP3 22050Hz 32kbps
* `mp3_44100_64` — MP3 44100Hz 64kbps
* `mp3_44100_128` — MP3 44100Hz 128kbps (рекомендуется)
* `mp3_44100_192` — MP3 44100Hz 192kbps

### Пример

```bash theme={null}
curl -X POST "https://polza.ai/api/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "elevenlabs/sound-effect-v2",
    "input": "sound of guitar strumming",
    "duration_seconds": 2.5,
    "loop": false,
    "output_format": "mp3_44100_128",
    "prompt_influence": 0.3
  }'
```

<Note>
  Описание звуковых эффектов должно быть на английском языке.
</Note>


## OpenAPI

````yaml POST /v1/audio/speech
openapi: 3.0.0
info:
  title: Polza.ai API
  description: AI агрегатор — унифицированный доступ к сотням AI моделей
  version: '1.0'
  contact: {}
servers:
  - url: https://polza.ai/api
    description: Production
security: []
tags: []
paths:
  /v1/audio/speech:
    post:
      tags:
        - Аудио
      summary: Сгенерировать речь из текста (TTS)
      operationId: AudioTtsController_createSpeech[3]
      parameters: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AudioSpeechDto'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioSpeechPresenter'
        '400':
          description: Некорректный запрос. Проверьте параметры и тело
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '401':
          description: Ошибка авторизации. Проверьте ключ доступа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '402':
          description: Недостаточно средств или достигнут лимит
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '403':
          description: Ошибка доступа. Проверьте права доступа ключа
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '404':
          description: Ресурс не найден
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '408':
          description: Истекло время ожидания ответа. Повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '409':
          description: Конфликт состояния. Перечитайте ресурс и повторите запрос
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '413':
          description: Размер тела запроса превышает допустимый предел
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '429':
          description: Слишком много запросов. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '500':
          description: Ошибка сервера. Обратитесь к поставщику услуг
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '502':
          description: Поставщик услуг вернул некорректный ответ
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
        '503':
          description: Сервис временно недоступен. Повторите позже
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiErrorPresenter'
      security:
        - bearer: []
components:
  schemas:
    AudioSpeechDto:
      type: object
      properties:
        model:
          type: string
          description: ID модели для генерации речи
          example: tts-1
          default: tts-1
        input:
          type: string
          description: Текст для озвучивания (максимум 5000 символов)
          example: Привет! Это тестовое сообщение.
          maxLength: 5000
        voice:
          type: string
          description: >-
            Голос для генерации речи. Допустимые значения зависят от модели:
            OpenAI (alloy, ash, ballad, coral, echo, fable, onyx, nova, sage,
            shimmer, verse), ElevenLabs (Rachel, Aria, Roger, Sarah и др.)
          example: alloy
        instructions:
          type: string
          description: >-
            Инструкции для управления характеристиками голоса. Поддерживается
            только для gpt-4o-mini-tts, не работает с tts-1 и tts-1-hd
          example: Говори медленно и выразительно
          maxLength: 4096
        response_format:
          type: string
          description: Формат выходного аудио
          enum:
            - mp3
            - opus
            - aac
            - flac
            - wav
            - pcm
          default: mp3
        speed:
          type: number
          description: Скорость генерации речи (0.25 - 4.0)
          example: 1
          minimum: 0.25
          maximum: 4
          default: 1
        stream_format:
          type: string
          description: >-
            Формат потоковой передачи аудио. Не поддерживается для tts-1 и
            tts-1-hd
          enum:
            - sse
            - audio
        user:
          type: string
          description: >-
            Уникальный идентификатор конечного пользователя для отслеживания и
            предотвращения злоупотреблений
          example: user-123
        stability:
          type: number
          description: Стабильность голоса (0-1). Только для ElevenLabs
          example: 0.5
          minimum: 0
          maximum: 1
        similarity_boost:
          type: number
          description: Усиление схожести голоса (0-1). Только для ElevenLabs
          example: 0.75
          minimum: 0
          maximum: 1
        style:
          type: number
          description: Экспрессия стиля (0-1). Только для ElevenLabs
          example: 0
          minimum: 0
          maximum: 1
        timestamps:
          type: boolean
          description: Возвращать временные метки для каждого слова. Только для ElevenLabs
          example: false
        previous_text:
          type: string
          description: >-
            Предшествующий текст для улучшения непрерывности речи при
            конкатенации. Только для ElevenLabs
          maxLength: 5000
        next_text:
          type: string
          description: >-
            Последующий текст для улучшения непрерывности речи при конкатенации.
            Только для ElevenLabs
          maxLength: 5000
        language_code:
          type: string
          description: Код языка ISO 639-1. Для ElevenLabs Turbo v2.5 и MiniMax Speech
          example: ru
          maxLength: 10
        emotion:
          type: string
          description: >-
            Эмоциональная окраска речи. Только для MiniMax Speech (neutral,
            happy, sad, angry, fearful, disgusted, surprised)
          example: happy
          maxLength: 20
        provider:
          description: Настройки выбора провайдера. В multipart-форме — JSON-строкой
          allOf:
            - $ref: '#/components/schemas/ProviderDto'
      required:
        - input
        - voice
    AudioSpeechPresenter:
      type: object
      properties:
        audio:
          type: string
          description: Base64-encoded аудио данные
          example: SUQzBAAAAAAAI1RTU0UAAA...
        contentType:
          type: string
          description: Content-Type аудио
          example: audio/mpeg
        model:
          type: string
          description: ID использованной модели
          example: tts-1
        duration:
          type: number
          description: Длительность аудио в секундах (если известна)
          example: 5.2
        usage:
          type: object
          description: Информация об использовании
          example:
            characters: 100
            cost: 0.01
            cost_rub: 0.01
        alignment:
          type: object
          description: 'Временные метки символов (при timestamps: true, ElevenLabs)'
      required:
        - audio
        - contentType
        - model
    ApiErrorPresenter:
      type: object
      properties:
        error:
          description: Информация об ошибке
          allOf:
            - $ref: '#/components/schemas/ApiErrorBodyPresenter'
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
      required:
        - error
    ProviderDto:
      type: object
      properties:
        require_parameters:
          type: boolean
          description: Требовать от OpenRouter поддержку всех переданных параметров
          example: true
        allow_fallbacks:
          type: boolean
          description: Разрешить использование резервных провайдеров
          example: true
        order:
          description: Упорядоченный список slug провайдеров для использования
          example:
            - OpenAI
            - Anthropic
          type: array
          items:
            type: string
        only:
          description: Список разрешенных slug провайдеров
          example:
            - OpenAI
            - Google
          type: array
          items:
            type: string
        ignore:
          description: Список игнорируемых slug провайдеров
          example:
            - DeepInfra
          type: array
          items:
            type: string
        sort:
          type: string
          description: Критерий сортировки провайдеров
          enum:
            - price
            - throughput
            - latency
          example: price
        max_price:
          description: Максимальные цены для запроса
          allOf:
            - $ref: '#/components/schemas/ProviderMaxPriceDto'
    ApiErrorBodyPresenter:
      type: object
      properties:
        code:
          type: string
          description: Код ошибки
          enum:
            - BAD_REQUEST
            - UNAUTHORIZED
            - api_key_revoked
            - INSUFFICIENT_BALANCE
            - FORBIDDEN
            - NOT_FOUND
            - REQUEST_TIMEOUT
            - CONFLICT
            - PAYLOAD_TOO_LARGE
            - TOO_MANY_REQUESTS
            - BAD_GATEWAY
            - SERVICE_UNAVAILABLE
            - INTERNAL_ERROR
          example: BAD_REQUEST
        message:
          type: string
          description: Описание ошибки
          example: Недопустимое значение параметра
        trace_id:
          type: string
          description: ID трассировки запроса
          example: 550e8400-e29b-41d4-a716-446655440000
        details:
          type: object
          description: Уточняющие поля ошибки. Отдаются только для 4xx
          additionalProperties: true
        metadata:
          description: Метаданные ошибки провайдера
          allOf:
            - $ref: '#/components/schemas/ApiErrorMetadataPresenter'
      required:
        - code
        - message
    ProviderMaxPriceDto:
      type: object
      properties:
        prompt:
          type: number
          description: Максимальная цена за промпт токены (RUB за миллион токенов)
          example: 10
        completion:
          type: number
          description: Максимальная цена за completion токены (RUB за миллион токенов)
          example: 20
        image:
          type: number
          description: Максимальная цена за изображение (RUB за штуку)
          example: 5
        audio:
          type: number
          description: Максимальная цена за аудио (RUB за миллион токенов)
          example: 15
        request:
          type: number
          description: Максимальная цена за запрос (RUB за запрос)
          example: 1
        video_per_second:
          type: number
          description: Максимальная цена за секунду видео (RUB за секунду)
          example: 50
        stt_per_minute:
          type: number
          description: Максимальная цена распознавания речи (RUB за минуту)
          example: 5
        tts_per_million_characters:
          type: number
          description: Максимальная цена синтеза речи (RUB за миллион символов)
          example: 1500
    ApiErrorMetadataPresenter:
      type: object
      properties:
        reason:
          type: string
          description: 'Машинная причина отказа: по ней можно ветвиться, не разбирая текст'
          example: noProvidersForModel
        raw:
          type: string
          description: Исходный текст ответа провайдера
          example: The parameter `duration` specified in the request is not valid
        provider_name:
          type: string
          description: Провайдер, вернувший ошибку
          example: openrouter
        attempts:
          description: Кого перебрали, прежде чем отказать
          type: array
          items:
            $ref: '#/components/schemas/ApiErrorAttemptPresenter'
    ApiErrorAttemptPresenter:
      type: object
      properties:
        provider:
          type: string
          description: Провайдер, к которому обращались
          example: OpenRouter
        reason:
          type: string
          description: Машинная причина отказа провайдера
          example: RATE_LIMIT
      required:
        - provider
        - reason
  securitySchemes:
    bearer:
      scheme: bearer
      bearerFormat: API Key
      type: http
      description: >-
        API ключ передаётся в заголовке: Authorization: Bearer
        <POLZA_AI_API_KEY>

````