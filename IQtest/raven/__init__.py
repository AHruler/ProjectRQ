from otree.api import *

doc = """
Your app description
"""


class Qs(ExtraModel):
    img_name = models.StringField()
    solution = models.StringField()
    key = models.StringField()


def load_matrices():
    rows = read_csv(__name__ + '/raven_m.csv', Qs)
    for row in rows:
        row['image_path'] = 'img/{}.jpg'.format(row['img_name'])
    return rows


class C(BaseConstants):
    NAME_IN_URL = 'Raven'
    PLAYERS_PER_GROUP = None
    MATRICES = load_matrices()
    NUM_ROUNDS = len(MATRICES)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    key = models.StringField()
    spa_8 = models.IntegerField(widget=widgets.RadioSelectHorizontal, choices=[1, 2, 3, 4, 5, 6, 7, 8],
                                label='', blank=True)
    spa_6 = models.IntegerField(widget=widgets.RadioSelectHorizontal, choices=[1, 2, 3, 4, 5, 6],
                                label='', blank=True)
    difficulty = models.IntegerField(choices=[1, 2, 3, 4, 5], widget=widgets.RadioSelectHorizontal)
    is_correct = models.BooleanField()


class record_diff(ExtraModel):
    player = models.Link(Player)
    difficulty = models.IntegerField()
    image = models.StringField()
    solution = models.StringField()
    choice = models.StringField()
    correct = models.BooleanField()
    total_correct = models.IntegerField()


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        img = get_current_m(p)
        p.key = img['key']


def get_current_m(player: Player):
    return C.MATRICES[player.round_number - 1]


# PAGES
class MainPage(Page):
    form_model = 'player'
    timeout_seconds = 120

    @staticmethod
    def get_form_fields(player):
        if player.key == '8':
            return ['spa_8', 'difficulty']
        else:
            return ['spa_6', 'difficulty']

    @staticmethod
    def vars_for_template(player: Player):
        matrix = get_current_m(player)
        return dict(matrix=matrix)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        matrix = get_current_m(player)
        player.is_correct = player.key == str(matrix['solution'])
        if player.key == '8':
            choice = player.spa_8
        else:
            choice = player.spa_6
        record_diff.create(player=player, difficulty=player.difficulty, image=matrix['img_name'],
                           solution=matrix['solution'], correct=player.is_correct, choice=choice)


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(num_correct=sum([p.is_correct for p in player.in_all_rounds()]),
                    num_incorrect=sum([not p.is_correct for p in player.in_all_rounds()]))


def custom_export(players):
    """For data export page"""

    yield ['player_id', 'img_name', 'key', 'difficulty', 'is_correct', 'solution',
           'choice']
    responses = record_diff.filter()

    for resp in responses:
        player = resp.player
        participant = player.participant
        yield [participant.id_in_session, resp.image, player.key, resp.difficulty, player.is_correct, resp.solution,
               resp.choice]

page_sequence = [MainPage, Results]
