import json
import os
import random
import string
from datetime import datetime

import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Ito Game",
    page_icon="🎮",
    layout="wide"
)

# Arquivo para armazenar estado dos jogos
GAMES_FILE = "games_state.json"


def load_games():
    """Carrega o estado dos jogos do arquivo JSON"""
    if os.path.exists(GAMES_FILE):
        try:
            with open(GAMES_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_games(games):
    """Salva o estado dos jogos no arquivo JSON"""
    with open(GAMES_FILE, 'w') as f:
        json.dump(games, f, indent=2)


def generate_room_code():
    """Gera um código único para a sala"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_new_game(room_code, players, max_rounds=5):
    """Cria um novo jogo"""
    return {
        'room_code': room_code,
        'players': players,
        'current_round': 1,
        'max_rounds': max_rounds,
        'cards_per_round': {},
        'results': {},
        'created_at': datetime.now().isoformat(),
        'status': 'waiting'  # waiting, playing, finished
    }


def distribute_cards(players, round_num, card_range=(1, 100)):
    """Distribui cartas para os jogadores"""
    num_players = len(players)
    cards_needed = num_players * round_num
    if cards_needed > (card_range[1] - card_range[0] + 1):
        st.error(f"Não há cartas suficientes para {num_players} jogadores na rodada {round_num}")
        return None

    all_cards = list(range(card_range[0], card_range[1] + 1))
    selected_cards = random.sample(all_cards, cards_needed)

    # Distribui as cartas entre os jogadores
    player_cards = {}
    for i, player in enumerate(players):
        player_cards[player] = selected_cards[i*round_num:(i+1)*round_num]

    return player_cards


def main():
    st.title("🎮 Ito Game")
    st.markdown("---")

    # Parâmetros da URL
    query_params = st.query_params
    room_code = query_params.get("room", "")
    player_id = query_params.get("player", "")

    games = load_games()

    # Sidebar para navegação
    st.sidebar.title("🎯 Menu")

    if room_code and room_code in games:
        # Se já está em uma sala válida
        game = games[room_code]

        if player_id:
            # Visualização do jogador individual
            st.sidebar.success(f"Sala: {room_code}")
            st.sidebar.info(f"Você é: {player_id}")
            show_player_view(game, player_id)
        else:
            # Visualização do administrador da sala
            st.sidebar.success(f"Administrando: {room_code}")
            show_admin_view(room_code, game, games)
    else:
        # Menu principal
        option = st.sidebar.selectbox(
            "Escolha uma opção:",
            ["🏠 Início", "🆕 Criar Sala", "🚪 Entrar em Sala"]
        )

        if option == "🆕 Criar Sala":
            show_create_room()
        elif option == "🚪 Entrar em Sala":
            show_join_room(games)
        else:
            show_home()


def show_home():
    """Tela inicial"""
    st.header("Bem-vindo ao Ito Game! 🎯")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Como Jogar:")
        st.markdown("""
        1. **Crie uma sala** ou **entre em uma existente**
        2. **Cada jogador** recebe cartas numeradas (1-100)
        3. **Escolham uma categoria** (ex: comidas, animais, marcas, etc)
        4. **Cada jogador** escolhe items da categoria com a nota dos seus números
        5. **Discutam** e decidam a ordem dos items
        6. **Verifiquem** se acertaram a ordem!
        """)

    with col2:
        st.subheader("🎮 Regras:")
        st.markdown("""
        - **Rodada 1:** 1 carta por jogador
        - **Rodada 2:** 2 cartas por jogador
        - **Rodada 3:** 3 cartas por jogador
        - **E assim por diante...**

        **Objetivo:** Colocar os items na ordem crescente dos números secretos!
        """)


def show_create_room():
    """Interface para criar uma nova sala"""
    st.header("🆕 Criar Nova Sala")

    with st.form("create_room_form"):
        col1, col2 = st.columns(2)

        with col1:
            num_players = st.number_input(
                "Número de jogadores:",
                min_value=2,
                max_value=8,
                value=4
            )

        with col2:
            max_rounds = st.number_input(
                "Número máximo de rodadas:",
                min_value=1,
                max_value=10,
                value=5
            )

        # Campos para nomes dos jogadores
        st.subheader("Nomes dos Jogadores")
        player_names = []
        cols = st.columns(2)
        for i in range(num_players):
            with cols[i % 2]:
                name = st.text_input(
                    f"Nome do Jogador {i+1}:",
                    value=f"Jogador {i+1}",
                    key=f"player_name_{i}"
                )
                player_names.append(name)

        submitted = st.form_submit_button("🎯 Criar Sala")

        if submitted:
            games = load_games()
            room_code = generate_room_code()

            # Garante que o código seja único
            while room_code in games:
                room_code = generate_room_code()

            game = create_new_game(room_code, player_names, max_rounds)
            games[room_code] = game
            save_games(games)

            st.success(f"✅ Sala criada com sucesso!")
            st.info(f"🔑 Código da sala: **{room_code}**")

            st.markdown("### 📱 Links para os jogadores:")

            # URLs para cada jogador
            base_url = "itocardgame.streamlit.app"  # Mude para sua URL quando fizer deploy

            for i, player in enumerate(player_names):
                encoded_name = player.replace(" ", "%20")
                player_url = f"{base_url}/?room={room_code}&player={encoded_name}"
                st.markdown(f"**{player}:** [{player_url}]({player_url})")

            # URL do administrador
            admin_url = f"{base_url}/?room={room_code}"
            st.markdown(f"**🎮 Administrador:** [{admin_url}]({admin_url})")


def show_join_room(games):
    """Interface para entrar em uma sala existente"""
    st.header("🚪 Entrar em Sala")

    if not games:
        st.warning("Não há salas ativas no momento.")
        return

    # Lista salas ativas
    active_rooms = {k: v for k, v in games.items() if v['status'] != 'finished'}

    if not active_rooms:
        st.warning("Não há salas ativas no momento.")
        return

    room_code = st.selectbox(
        "Escolha uma sala:",
        options=list(active_rooms.keys()),
        format_func=lambda x: f"{x} - {len(active_rooms[x]['players'])} jogadores"
    )

    if st.button("🎯 Entrar na Sala"):
        st.query_params.room = room_code
        st.rerun()


def show_admin_view(room_code, game, games):
    """Interface do administrador da sala"""
    st.header(f"🎮 Administrador - Sala {room_code}")

    # Status do jogo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rodada Atual", f"{game['current_round']}/{game['max_rounds']}")
    with col2:
        st.metric("Jogadores", len(game['players']))
    with col3:
        st.metric("Status", game['status'].title())

    st.markdown("---")

    # Controles do jogo
    if game['status'] == 'waiting':
        st.subheader("🎯 Iniciar Rodada")

        if st.button("🚀 Distribuir Cartas para Rodada Atual"):
            current_round = game['current_round']
            cards = distribute_cards(game['players'], current_round)

            if cards:
                game['cards_per_round'][str(current_round)] = cards
                game['status'] = 'playing'
                games[room_code] = game
                save_games(games)

                st.success(f"✅ Cartas distribuídas para rodada {current_round}!")
                st.rerun()

    elif game['status'] == 'playing':
        current_round = game['current_round']
        st.subheader(f"🎮 Rodada {current_round} em Andamento")

        # Mostrar cartas distribuídas (apenas para admin)
        if str(current_round) in game['cards_per_round']:
            with st.expander("👁️ Ver Cartas Distribuídas (Admin)"):
                cards = game['cards_per_round'][str(current_round)]
                for player, player_cards in cards.items():
                    st.write(f"**{player}:** {sorted(player_cards)}")

        st.markdown("### ✅ Verificar Ordem")

        # Input da ordem jogada
        with st.form("verify_order"):
            st.write("Digite a ordem em que os items foram colocados:")

            total_cards = len(game['players']) * current_round
            # Create selection boxes for each position
            st.write(f"Selecione o jogador para cada posição (total: {total_cards} posições):")

            player_selections = []
            cols = st.columns(min(3, total_cards))
            unique_players = list(game['players'])
            for i in range(total_cards):
                with cols[i % 3]:
                    selection = st.selectbox(
                        f"Posição {i + 1}",
                        options=unique_players,
                        key=f"pos_{i}"
                    )
                    player_selections.append(selection)

            submitted = st.form_submit_button("🔍 Verificar Ordem")

            if submitted:
                try:
                    # Convert player selections to their corresponding numbers
                    played_order = []
                    round_cards = game['cards_per_round'][str(current_round)]

                    for player in player_selections:
                        # Get the player's unused card with the lowest value
                        player_cards = sorted(round_cards[player])
                        card = player_cards[sum(1 for p in player_selections[:len(played_order)] if p == player)]
                        played_order.append(card)

                    if len(played_order) != total_cards:
                        st.error(f"Você deve inserir exatamente {total_cards} números!")
                    else:
                        # Verificar se a ordem está correta
                        cards = game['cards_per_round'][str(current_round)]
                        all_cards = []
                        for player_cards in cards.values():
                            all_cards.extend(player_cards)

                        correct_order = sorted(all_cards)
                        is_correct = played_order == correct_order

                        # Salvar resultado
                        game['results'][str(current_round)] = {
                            'played_order': played_order,
                            'correct_order': correct_order,
                            'is_correct': is_correct,
                            'timestamp': datetime.now().isoformat()
                        }

                        # Salvar no session state para controlar a revelação
                        if 'card_reveal' not in st.session_state:
                            st.session_state.card_reveal = {
                                'round': current_round,
                                'correct_order': correct_order,
                                'played_order': played_order,
                                'current_card': 0,
                                'is_correct': is_correct
                            }

                        games[room_code] = game
                        save_games(games)
                        st.rerun()
   
                except ValueError:
                    st.error("Por favor, insira apenas números separados por vírgula!")

        # SISTEMA DE REVELAÇÃO INTERATIVA
        if 'card_reveal' in st.session_state:
            st.markdown("---")
            reveal_data = st.session_state.card_reveal

            if reveal_data['current_card'] < len(reveal_data['correct_order']):
                # Ainda há cartas para revelar
                st.subheader(f"🎴 Revelação das Cartas - Posição {reveal_data['current_card'] + 1}")

                # Mostrar cartas já reveladas
                if reveal_data['current_card'] > 0:
                    st.markdown("### 🔍 Cartas já reveladas:")

                    cols = st.columns(min(reveal_data['current_card'], 6))
                    for i in range(reveal_data['current_card']):
                        col_index = i % 6
                        with cols[col_index]:
                            card = reveal_data['correct_order'][i]
                            played_card = reveal_data['played_order'][i] if i < len(reveal_data['played_order']) else None

                            # Determinar se está correto
                            if played_card == card:
                                bg_color = "linear-gradient(45deg, #4CAF50, #45a049)"
                                status = "✅"
                                result_text = "CORRETO!"
                            else:
                                bg_color = "linear-gradient(45deg, #f44336, #da190b)"
                                status = "❌"
                                result_text = f"Era {played_card if played_card else '?'}"

                            st.markdown(f"""
                            <div style='
                                background: {bg_color};
                                color: white;
                                padding: 15px;
                                border-radius: 10px;
                                text-align: center;
                                font-size: 16px;
                                font-weight: bold;
                                margin: 5px;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                            '>
                                {status}<br>
                                <span style='font-size: 24px;'>{card}</span><br>
                                <small>{result_text}</small>
                            </div>
                            """, unsafe_allow_html=True)

                # Botão para revelar próxima carta
                st.markdown("---")
                next_card = reveal_data['correct_order'][reveal_data['current_card']]

                if st.button(f"🎯 Revelar Carta da Posição {reveal_data['current_card'] + 1}", 
                           key=f"reveal_{reveal_data['current_card']}", 
                           type="primary"):
                    st.session_state.card_reveal['current_card'] += 1
                    st.rerun()

            else:
                # Todas as cartas foram reveladas
                st.subheader("🏁 Revelação Completa!")

                # Resultado final
                if reveal_data['is_correct']:
                    st.success("🎉 PARABÉNS! Vocês acertaram TODAS as cartas!")
                    st.balloons()
                else:
                    correct_count = sum(1 for i in range(len(reveal_data['played_order'])) 
                                      if i < len(reveal_data['correct_order']) and 
                                      reveal_data['played_order'][i] == reveal_data['correct_order'][i])
                    st.warning(f"😅 Vocês acertaram {correct_count} de {len(reveal_data['correct_order'])} cartas!")

                # Mostrar todas as cartas finais
                st.markdown("### 📋 Resultado Final:")
                cols = st.columns(min(len(reveal_data['correct_order']), 6))
                for i, card in enumerate(reveal_data['correct_order']):
                    col_index = i % 6
                    with cols[col_index]:
                        played_card = reveal_data['played_order'][i] if i < len(reveal_data['played_order']) else None

                        if played_card == card:
                            bg_color = "linear-gradient(45deg, #4CAF50, #45a049)"
                            status = "✅"
                            result_text = "CORRETO!"
                        else:
                            bg_color = "linear-gradient(45deg, #f44336, #da190b)"
                            status = "❌"
                            result_text = f"Era {played_card if played_card else '?'}"

                        st.markdown(f"""
                        <div style='
                            background: {bg_color};
                            color: white;
                            padding: 15px;
                            border-radius: 10px;
                            text-align: center;
                            font-size: 16px;
                            font-weight: bold;
                            margin: 5px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                        '>
                            {status}<br>
                            <span style='font-size: 24px;'>{card}</span><br>
                            <small>{result_text}</small>
                        </div>
                        """, unsafe_allow_html=True)

                # Botão para continuar
                st.markdown("---")
                if st.button("➡️ Continuar para Próxima Rodada", type="primary"):
                    # Limpar estado da revelação
                    del st.session_state.card_reveal

                    # Próxima rodada ou fim do jogo
                    if current_round < game['max_rounds']:
                        game['current_round'] += 1
                        game['status'] = 'waiting'
                    else:
                        game['status'] = 'finished'

                    games[room_code] = game
                    save_games(games)
                    st.rerun()

    elif game['status'] == 'finished':
        st.subheader("🏁 Jogo Finalizado!")
        show_game_results(game)

    # Botão para reiniciar o jogo
    st.markdown("---")
    if st.button("🔄 Reiniciar Jogo"):
        # Limpar estado da revelação se existir
        if 'card_reveal' in st.session_state:
            del st.session_state.card_reveal

        game['current_round'] = 1
        game['status'] = 'waiting'
        game['cards_per_round'] = {}
        game['results'] = {}
        games[room_code] = game
        save_games(games)
        st.rerun()


def show_player_view(game, player_id):
    """Interface individual do jogador"""
    st.header(f"🎯 {player_id}")

    current_round = game['current_round']

    # Status da rodada
    st.subheader(f"Rodada {current_round}")

    # Always show refresh button
    if st.button("🔄 Ver cartas"):
        st.rerun()

    if game['status'] == 'waiting':
        st.info("⏳ Aguardando o administrador distribuir as cartas...")

    elif game['status'] == 'playing':
        # Mostrar cartas do jogador
        if str(current_round) in game['cards_per_round']:
            cards = game['cards_per_round'][str(current_round)]

            if player_id in cards:
                player_cards = sorted(cards[player_id])

                st.success("🎴 Suas cartas:")

                # Mostrar cartas em destaque
                cols = st.columns(len(player_cards))
                for i, card in enumerate(player_cards):
                    with cols[i]:
                        st.markdown(f"""
                        <div style='
                            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                            color: white;
                            padding: 20px;
                            border-radius: 10px;
                            text-align: center;
                            font-size: 24px;
                            font-weight: bold;
                            margin: 5px;
                        '>
                            {card}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                st.info("💡 Agora escolham uma categoria e discutam presencialmente!")
            else:
                st.warning("Você não está registrado neste jogo.")
        else:
            st.warning("Cartas ainda não foram distribuídas.")

    elif game['status'] == 'finished':
        st.success("🏁 Jogo finalizado!")
        show_game_results(game)


def show_game_results(game):
    """Mostra os resultados do jogo"""
    st.subheader("📊 Resultados do Jogo")

    if not game['results']:
        st.info("Nenhum resultado registrado ainda.")
        return

    total_rounds = len(game['results'])
    correct_rounds = sum(1 for result in game['results'].values() if result['is_correct'])

    st.metric("Score Final", f"{correct_rounds}/{total_rounds}")

    # Detalhes por rodada
    for round_num, result in game['results'].items():
        with st.expander(f"Rodada {round_num} - {'✅ Correto' if result['is_correct'] else '❌ Incorreto'}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Ordem jogada:**")
                st.write(result['played_order'])
            with col2:
                st.write("**Ordem correta:**")
                st.write(result['correct_order'])


if __name__ == "__main__":
    main()
