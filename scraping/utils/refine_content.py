from bs4 import BeautifulSoup


##############
# REMOVE IMG #
##############

def remove_img(soup: BeautifulSoup):
    for s in soup.select('img'):
        s.extract()

    for s in soup.select('svg'):
        s.extract()

    return soup


###################
# CONVERT TO TEXT #
###################

def is_table(element):
    # TODO
    return False


def is_link(element):
    # TODO
    return False


def is_span(element):
    # TODO
    return False


def is_text(element):
    # TODO
    return True


def get_element_and_text(element):
    # TODO
    return element.find_all()


def build_text(soup: BeautifulSoup):
    if is_table(soup):
        # TODO return table HTML
        return soup

    if is_link(soup):
        # TODO return link HTML
        return soup

    if is_span(soup):
        # TODO return span text
        return soup.text

    if is_text(soup):
        # TODO return text
        return soup.text

    # TODO Iterate on each element and text
    return '\n'.join(map(build_text, get_element_and_text(soup)))


########
# MAIN #
########

def refine_confession_content(content_html):
    if content_html is None:
        return None

    soup = BeautifulSoup(content_html, 'html.parser')
    soup = remove_img(soup)

    return soup.prettify()

if __name__ == '__main__':
    html = """
<body><div id="above-content">
 <div id="portal-breadcrumbs">
  <span id="breadcrumbs-home">
   <a href="https://www.laredemption-stjoseph.fr">
    Accueil
   </a>
   <span class="breadcrumbSeparator">
    ›
   </span>
  </span>
  <span dir="ltr" id="breadcrumbs-1">
   <a href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne">
    Etapes de la vie chrétienne
   </a>
   <span class="breadcrumbSeparator">
    ›
   </span>
  </span>
  <span dir="ltr" id="breadcrumbs-2">
   <a href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/reconciliation-et-penitence">
    Réconciliation et Pénitence
   </a>
  </span>
  <span>
  </span>
 </div>
 <div class="row" id="portlets-above">
 </div>
</div>
<br>
<div id="portal-column-one">
</div>
<br>
<div id="portal-column-two">
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736561726368 portletNumber-0 portlet-search" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736561726368" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736561726368">
  <dl class="portlet portletSearch">
   <dt class="portletHeader">
    <span class="portletTopLeft">
    </span>
    <a class="tile" href="https://www.laredemption-stjoseph.fr/@@search">
     Recherche
    </a>
    <span class="portletTopRight">
    </span>
   </dt>
   <dd class="portletItem">
    <form action="https://www.laredemption-stjoseph.fr/@@search" id="searchform">
     <div class="LSBox">
      <input class="searchField portlet-search-gadget-nols" name="SearchableText" placeholder="Recherche" size="15" title="Chercher dans le site" type="text">
      <input class="searchButton" type="submit" value="Rechercher">
     </div>
    </form>
    <div class="visualClear">
     <!-- -->
    </div>
   </dd>
   <dd class="portletFooter">
    <a class="tile" href="https://www.laredemption-stjoseph.fr/@@search">
     Recherche avancée…
    </a>
    <span class="portletBottomLeft">
    </span>
    <span class="portletBottomRight">
    </span>
   </dd>
  </dl>
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a62756c6c6574696e2d7061726f69737369616c portletNumber-1 portlet-bulletin-paroissial" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a62756c6c6574696e2d7061726f69737369616c" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a62756c6c6574696e2d7061726f69737369616c">
  <div class="portletBSWNewsletterSubscriber">
   <span>
    Bulletin paroissial
   </span>
   <p>
    Abonnez-vous à notre newsletter pour recevoir le bulletin hebdomadaire
   </p>
   <form action="https://www.laredemption-stjoseph.fr/newsletter/abonnes/abonne_edit?nl=newsletter-principale" id="inscription" method="post" name="inscription">
    <input id="email-portlet-inscription-newsletter" name="email" placeholder="Saisissez votre email" type="text">
    <input alt="s'inscrire" class="standalone" id="bt-portlet-inscription-newsletter" name="subscribe" type="submit" value="s'inscrire">
   </form>
  </div>
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6e617669676174696f6e portletNumber-2 portlet-navigation" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6e617669676174696f6e" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6e617669676174696f6e">
  <dl class="portlet portletNavigationTree">
   <dt class="portletHeader hiddenStructure">
    <span class="portletTopLeft">
    </span>
    <a class="tile" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/sitemap">
     Navigation
    </a>
    <span class="portletTopRight">
    </span>
   </dt>
   <dd class="portletItem lastItem">
    <ul class="navTree navTreeLevel0">
     <li class="navTreeItem navTreeTopNode">
      <div>
       <a class="contenttype-plone-site" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne" title="">
        Etapes de la vie chrétienne
       </a>
      </div>
     </li>
     <li class="navTreeItem visualNoMarker section-les-7-sacrements">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/les-7-sacrements" title="Qu'est-ce qu'un sacrement ? Et pourquoi les célébrer ?">
       <span>
        Les 7 sacrements
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-le-bapteme">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/le-bapteme" title="">
       <span>
        Le Baptême
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-la-confirmation">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/la-confirmation" title="&quot;Vous allez recevoir une force quand le Saint-Esprit viendra sur vous ; vous serez alors mes témoins à Jérusalem, dans toute la Judée et la Samarie, et jusqu’aux extrémités de la terre.&quot; (Ac 1, 8)">
       <span>
        La Confirmation
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-leucharistie">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/leucharistie" title="« Je suis venu pour que les hommes aient la vie et qu’ils l'aient en abondance. » (Jn 10, 10)">
       <span>
        L'Eucharistie
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-la-premiere-communion">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/la-premiere-communion" title="Recevoir le Christ dans le sacrement de l'Eucharistie">
       <span>
        La Première Communion
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker navTreeCurrentNode section-reconciliation-et-penitence">
      <a class="state-published navTreeCurrentItem navTreeCurrentNode contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/reconciliation-et-penitence" title="&quot;Je ne suis pas venu appeler les justes mais les pécheurs&quot;
Se laisser réconcilier par le Christ">
       <span>
        Réconciliation et Pénitence
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-onction-des-malades">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/onction-des-malades" title="« Pour ceux qui souffrent dans leurs corps ou dans leurs cœurs… »">
       <span>
        Onction des malades
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-mariage">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/mariage" title="« L’homme s’attachera à sa femme, et tous deux ne feront plus qu’un. Ce mystère est grand : je le dis en référence au Christ et à l’Église » (Ep 5, 31-32).">
       <span>
        Mariage
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-lordre">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/lordre" title="Les prêtres que Dieu donne...">
       <span>
        L'Ordre
       </span>
      </a>
     </li>
     <li class="navTreeItem visualNoMarker section-les-funerailles">
      <a class="state-published contenttype-document" href="https://www.laredemption-stjoseph.fr/etapes-de-la-vie-chretienne/les-funerailles" title="&quot;Je ne meurs pas j'entre dans la vie&quot; Ste Thérèse de l'Enfant Jésus">
       <span>
        Les Funérailles
       </span>
      </a>
     </li>
    </ul>
    <span class="portletBottomLeft">
    </span>
    <span class="portletBottomRight">
    </span>
   </dd>
  </dl>
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a61637475616c69746573 portletNumber-3 portlet-actualites" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a61637475616c69746573" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a61637475616c69746573">
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6576656e656d656e7473 portletNumber-4 portlet-evenements" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6576656e656d656e7473" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a6576656e656d656e7473">
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a66696c6573 portletNumber-5 portlet-files" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a66696c6573" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a66696c6573">
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a616c62756d732d70686f746f73 portletNumber-6 portlet-albums-photos" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a616c62756d732d70686f746f73" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a616c62756d732d70686f746f73">
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736f6e73 portletNumber-7 portlet-sons" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736f6e73" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a736f6e73">
 </div>
 <div class="portletWrapper kssattr-portlethash-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a766964656f73 portletNumber-8 portlet-videos" data-portlethash="706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a766964656f73" id="portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f73746a6f736570680a766964656f73">
 </div>
</div>
<br>
<div id="portal-column-content">
 <dl class="portalMessage info" id="kssPortalMessage" style="display:none">
  <dt>
   Info
  </dt>
  <dd>
  </dd>
 </dl>
 <div id="content">
  <div id="viewlet-above-content-title">
  </div>
  <h1 class="documentFirstHeading" id="parent-fieldname-title">
   Réconciliation et Pénitence
  </h1>
  <div id="viewlet-below-content-title">
   <div class="row" id="portlets-below">
   </div>
  </div>
  <div class="documentDescription">
   "Je ne suis pas venu appeler les justes mais les pécheurs"
   <br>
    Se laisser réconcilier par le Christ
   <br>
  </div>
  <div id="viewlet-above-content-body">
  </div>
  <div id="content-core">
   <div class="" id="parent-fieldname-text-0dffd74be39c46a6ba805ec0186207e1">
    <p style="text-align: justify;">
     Recevoir le pardon du Christ pour nos péchés et la force de la miséricorde pour grandir dans la vie chrétienne.
    </p>
    <p style="text-align: justify;">
     Ce sacrement est le don de la libération du mal et de la croissance spirituelle.
    </p>
    <p style="text-align: justify;">
     Venez à la source de la miséricorde&nbsp;!
    </p>
    <p style="text-align: justify;">
     Ce sacrement est proposé (
     <em>
      <strong>
       hors vacances scolaires
      </strong>
     </em>
     ) :
    </p>
    <p style="text-align: center;">
     <u>
      <strong>
       Adoration et confessions
      </strong>
     </u>
    </p>
    <ul>
     <li>
      vendredi, de 18h à 19h, église de la Rédemption
     </li>
     <li>
      mercredi et jeudi&nbsp; à 18h30 confessions, église de la Rédemption
     </li>
    </ul>
    <p style="text-align: center;">
    </p>
    <p>
    </p>
   </div>
  </div>
  <div id="viewlet-below-content-body">
   <div class="visualClear">
    <!-- -->
   </div>
   <div class="documentActions">
   </div>
  </div>
 </div>
</div>
</body>
    """

    html2 = """
    <body><header class="entry-header">
 <div class="inner-wrap">
  <h1 class="entry-title">
   Confessions
  </h1>
 </div>
 <!-- .inner-wrap -->
</header>
<br>
<div class="entry-content">
 <blockquote class="wp-block-quote">
  <cite>
   «&nbsp;Dans&nbsp; le sacrement de pénitence, les fidèles qui confessent leurs péchés à un ministre légitime, en ont la contrition et forment le propos de s’amender, obtiennent de Dieu, par l’absolution donnée par ce même ministre, le pardon des péchés qu’ils ont commis après le baptême, et ils sont en même temps réconciliés avec l’Église qu’en péchant ils ont blessée&nbsp;» (canon 959).
  </cite>
 </blockquote>
 <blockquote class="wp-block-quote">
  <cite>
   CEC 1420
   <em>
    :
   </em>
   Par les sacrements de l’initiation chrétienne, l’homme reçoit la vie nouvelle du Christ. Or, cette vie, nous la portons &nbsp;»&nbsp;en des vases d’argile&nbsp;&nbsp;» (2 Co 4, 7). Maintenant, elle est encore &nbsp;»&nbsp;cachée avec le Christ en Dieu&nbsp;&nbsp;» (Col 3, 3). Nous sommes encore dans &nbsp;»&nbsp;notre demeure terrestre&nbsp;&nbsp;» (2 Co 5, 1) soumise à la souffrance, à la maladie et à la mort. Cette vie nouvelle d’enfant de Dieu peut être affaiblie et même perdue par le péché.
  </cite>
 </blockquote>
 <blockquote class="wp-block-quote">
  <cite>
   CEC 1421
   <em>
    :
   </em>
   Le Seigneur Jésus-Christ, médecin de nos âmes et de nos corps, Lui qui a remis les péchés au paralytique et lui a rendu la santé du corps (cf. Mc 2, 1-12), a voulu que son Église continue, dans la force de l’Esprit Saint, son œuvre de guérison et de salut, même auprès de ses propres membres. C’est le but des deux sacrements de guérison&nbsp;: du sacrement de Pénitence et de l’Onction des malades.
  </cite>
 </blockquote>
 <figure class="wp-block-table">
  <table class="has-background" style="background-color:#7bdbb538">
   <tbody>
    <tr>
     <td>
      <strong>
       Dimanche
      </strong>
     </td>
     <td>
      p
      <em>
       endant les messes
      </em>
      (sauf empêchement)
     </td>
    </tr>
    <tr>
     <td>
      <strong>
       Du lundi au vendredi
      </strong>
     </td>
     <td>
      de 17h30 à 18h15
     </td>
    </tr>
    <tr>
     <td>
      <strong>
       Samedi
      </strong>
     </td>
     <td>
      de 9h45 à 10h45
     </td>
    </tr>
    <tr>
     <td>
      <strong>
       sur rendez-vous
      </strong>
     </td>
     <td>
      auprès d’un prêtre (
      <a href="https://eglisesaintgeorges.com/pretres/">
       ici
      </a>
      )
     </td>
    </tr>
   </tbody>
  </table>
 </figure>
</div>
</body>
    """
