import flet as ft
from flet import TextField, IconButton, Icon, Container, Column, Row, ScrollMode, alignment
from cohere import Client
import qdrant_client
import numpy as np
from time import sleep
import threading

# Configuración de la API de Cohere
co = Client('KEU6Q0EelVAj3px3KVRA16E4oglZdwb63Yn9sDuC')

# Configuración de Qdrant
qdrant = qdrant_client.QdrantClient(
    url="https://a063d286-b561-49d2-b857-141de9938c15.us-east4-0.gcp.cloud.qdrant.io:6333", 
    api_key="BbWYd5Q9BULpgozU8Lf1UXmpuY9e5LyJ0zABUw0apRhQKYNFLYRUiQ",
)
# Nombre del índice en Qdrant
index_name = 'chat_bot_universidad'

# Preamble del chat
preamble = (
    "Eres un guía de información de la Universidad de las Fuerzas Armadas ESPE. "
    "Proporciona respuestas claras y detalladas a las consultas de los estudiantes específicamente sobre esta universidad. "
    "Si la pregunta no está relacionada con la Universidad de las Fuerzas Armadas ESPE, responde que no entendiste la pregunta o que no estás preparado para responderla."
)
# Dimensiones del vector en Qdrant
VECTOR_DIMENSION = 1024

class Message:
    def __init__(self, user_name: str, text: str, message_type: str, is_user: bool = False):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.is_user = is_user

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text, selectable=True, wrap=ft.TextWrap.WRAP),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"  # or any default value you prefer

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def truncate_vector(vector, size=VECTOR_DIMENSION):
    if len(vector) > size:
        return vector[:size]
    return vector

def show_loading_indicator(page: ft.Page, loading_indicator: ft.ProgressRing):
    loading_indicator.visible = True
    page.update()

def hide_loading_indicator(page: ft.Page, loading_indicator: ft.ProgressRing):
    loading_indicator.visible = False
    page.update()

def process_message(user_message: str, page: ft.Page, loading_indicator: ft.ProgressRing):
    show_loading_indicator(page, loading_indicator)
    
    # Generar embedding para el mensaje del usuario
    user_embedding = co.embed(texts=[user_message]).embeddings[0]
    truncated_embedding = truncate_vector(user_embedding)

    # Buscar en Qdrant
    search_results = qdrant.search(index_name, query_vector=truncated_embedding)

    chatbot_response = ""
    if search_results and 'result' in search_results and search_results['result']:
        chatbot_response = search_results['result'][0]['payload']['answer']
    else:
        # Generar respuesta con Cohere
        stream = co.chat_stream(message=user_message, model="command-r-plus", preamble=preamble)
        for event in stream:
            if event.event_type == "text-generation":
                chatbot_response += event.text

        # Almacenar el mensaje y la respuesta en Qdrant
        qdrant.upsert(
            collection_name=index_name,
            points=[
                {
                    "id": np.random.randint(0, 1e6),  # Generar un ID único para el punto
                    "vector": truncated_embedding,
                    "payload": {"answer": chatbot_response, "question": user_message}
                }
            ]
        )

    # Ocultar el indicador de carga
    hide_loading_indicator(page, loading_indicator)

    # Mostrar la pregunta del usuario
    page.pubsub.send_all(
        Message(
            user_name=page.session.get("user_name"),
            text=user_message,
            message_type="chat_message",
            is_user=True
        )
    )

    # Mostrar la respuesta del chatbot
    page.pubsub.send_all(
        Message(
            user_name="Chatbot",
            text=chatbot_response,
            message_type="chat_message",
        )
    )

def main(page: ft.Page):
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.title = "Chat Universitario"

    # Crear el indicador de carga
    loading_indicator = ft.ProgressRing(width=24, height=24, stroke_width=4, visible=False)

    def join_chat_click(e):
        if not join_user_name.value:
            join_user_name.error_text = "¡El nombre no puede estar vacío!"
            join_user_name.update()
        else:
            page.session.set("user_name", join_user_name.value)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{join_user_name.value}: ")
            page.pubsub.send_all(
                Message(
                    user_name=join_user_name.value,
                    text=f"{join_user_name.value} se ha unido al chat.",
                    message_type="login_message",
                )
            )
            page.update()

    def send_message_click(e):
        if new_message.value != "":
            user_message = new_message.value.strip()

            # Ejecutar el procesamiento del mensaje en un hilo separado para mantener la UI responsiva
            threading.Thread(target=process_message, args=(user_message, page, loading_indicator)).start()

            new_message.value = ""
            new_message.focus()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

    # Diálogo para pedir el nombre del usuario
    join_user_name = ft.TextField(
        label="Introduce tu nombre para unirte al chat",
        autofocus=True,
        on_submit=join_chat_click,
    )
    page.dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("¡Bienvenido!"),
        content=ft.Column([join_user_name], width=300, height=70, tight=True),
        actions=[ft.ElevatedButton(text="Unirse al chat", on_click=join_chat_click)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Mensajes del chat
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        scroll_mode=ScrollMode.AUTO,
    )

    # Formulario de entrada de nuevo mensaje
    new_message = ft.TextField(
        hint_text="Escribe un mensaje...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    # Añadir todo a la página
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Enviar mensaje",
                    on_click=send_message_click,
                ),
            ]
        ),
        loading_indicator,  # Añadir el indicador de carga a la página
    )

ft.app(target=main)
