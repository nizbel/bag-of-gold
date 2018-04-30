

class InserirForkTestCase(TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        bcash = Criptomoeda.objects.create(nome='Bitcoin Cash', ticker='BCH')
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.9662'), preco_unitario=Decimal('10000'), data=datetime.date(2017, 6, 6), 
                                                      tipo_operacao='C', criptomoeda=bitcoin, investidor=user.investidor)
        DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_1, divisao=Divisao.objects.get(investidor=user.investidor), quantidade=compra_1.quantidade)
        
    def test_usuario_deslogado(self):
        """Testa se redireciona ao receber usuário deslogado"""
        response = self.client.get(reverse('criptomoeda:inserir_fork'))
        self.assertEqual(response.status_code, 301)
        # TODO Verificar se resposta foi para tela de login
        self.assertEqual(response.url, 'login')
        
    def test_usuario_logado(self)
        """Testa se resposta da página está OK"""
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('criptomoeda:inserir_fork'))
        self.assertEqual(response.status_code, 200)
    
    def test_inserir_fork_sucesso(self):
        """Testa a inserção de fork com sucesso"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, reverse('criptomoeda:historico'))
        self.assertTrue(Fork.objects.get(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9662'), investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.get(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9662'), fork=Fork.objects.get(investidor=investidor))
        
    
    def test_inserir_fork_qtd_insuficiente(self):
        """Testa inserir fork com quantidade insuficiente de moeda de origem"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9663'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, reverse('criptomoeda:inserir_fork'))
    
    def test_inserir_fork_mesma_moeda(self):
        """Testa inserir fork inserindo a mesma moeda para origem e recebida"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bitcoin.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, reverse('criptomoeda:inserir_fork'))