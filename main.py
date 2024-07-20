import flet as ft
from flet import TextField, ElevatedButton, Text, Container, Column, Row, ScrollMode
from cohere import Client

# Configuración de la API de Cohere
co = Client('KEU6Q0EelVAj3px3KVRA16E4oglZdwb63Yn9sDuC')

# Preamble del chat
preamble = "You are a university information guide. Provide clear and detailed answers to student inquiries. If the question is not related to university information, respond that you did not understand the question or that you are not prepared to answer it."

# Función para manejar el envío de mensajes
def send_message(e):
    user_message = user_input.value.strip()
    if user_message.lower() == 'quit':
        page.window_destroy()
        return

    try:
        stream = co.chat_stream(message=user_message,
                                model="command-r-plus",
                                preamble=preamble)
        chatbot_response = ""
        for event in stream:
            if event.event_type == "text-generation":
                chatbot_response += event.text
        chat_window.controls.append(
            Row(
                controls=[
                    Container(Text(f"User: {user_message}"),
                              bgcolor=user_bg,
                              padding=10,
                              border_radius=10,
                              width=400,  # Limitar el ancho máximo
                              expand=True)
                ],
                alignment=ft.alignment.bottom_center,
            ))
        chat_window.controls.append(
            Row(
                controls=[
                    Container(Text(f"Chatbot: {chatbot_response}"),
                              bgcolor=chatbot_bg,
                              padding=10,
                              border_radius=10,
                              width=400,  # Limitar el ancho máximo
                              expand=True)
                ],
                alignment=ft.alignment.top_center,
            ))
        chat_window.update()
    except Exception as e:
        page.dialog = ft.AlertDialog(
            title=Text("Error"),
            content=Text(str(e)),
            actions=[
                ft.ElevatedButton(text="OK",
                                  on_click=lambda _: page.dialog.dismiss())
            ])
        page.dialog.open = True
        page.update()

    user_input.value = ""
    user_input.update()

# Configuración de la interfaz de usuario con Flet
def main(page: ft.Page):
    global user_input, chat_window, user_bg, chatbot_bg

    page.title = "Chatbot Universitario"
    page.scroll = ScrollMode.AUTO

    user_bg = '#5CACEE'  # Azul claro
    chatbot_bg = '#98FB98'  # Verde claro

    chat_window = Column(scroll=ScrollMode.AUTO)

    user_input = TextField(multiline=True,
                           min_lines=3,
                           max_lines=5,
                           expand=True)
    send_button = ElevatedButton(text="Enviar",
                                 on_click=send_message,
                                 bgcolor=user_bg,
                                 color='white')

    page.add(
        Container(
            content=Column(controls=[
                chat_window,
                Row([user_input, send_button], alignment="end")
            ],
                           expand=True,
                           spacing=10),
            expand=True,
            padding=10,
        ))

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
