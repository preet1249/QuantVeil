import WebsiteCard     from './cards/WebsiteCard'
import ContactsCard    from './cards/ContactsCard'
import RedditCard      from './cards/RedditCard'
import NewsCard        from './cards/NewsCard'
import GitHubCard      from './cards/GitHubCard'
import CrunchbaseCard  from './cards/CrunchbaseCard'
import MarketCard      from './cards/MarketCard'
import DownloadsCard   from './cards/DownloadsCard'

export default function ResultsPanel({ sections, jobId, isDone, pptMode }) {
  return (
    <>
      {sections.website    && <WebsiteCard    data={sections.website} />}
      {sections.contacts   && <ContactsCard   data={sections.contacts} />}
      {sections.reddit     && <RedditCard     data={sections.reddit} />}
      {sections.news       && <NewsCard       newsData={sections.news} wayback={sections.wayback} />}
      {sections.github     && <GitHubCard     data={sections.github} />}
      {sections.crunchbase && sections.crunchbase.found && <CrunchbaseCard data={sections.crunchbase} />}
      {(sections.cold_outreach || sections.market_research) && (
        <MarketCard
          coldOutreach={sections.cold_outreach?.text || ''}
          marketResearch={sections.market_research?.text || ''}
        />
      )}
      {isDone && (
        <DownloadsCard jobId={jobId} pptMode={pptMode} />
      )}
    </>
  )
}
