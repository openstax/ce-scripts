import fs from 'fs'
import path from 'path'

import { DOMParser } from 'xmldom'
import * as xpath from 'xpath-ts'

const NS_COLLECTION = 'http://cnx.rice.edu/collxml'
const NS_CNXML = 'http://cnx.rice.edu/cnxml'
const NS_METADATA = 'http://cnx.rice.edu/mdml'
const NS_CONTAINER = 'https://openstax.org/namespaces/book-container'

export function expectValue<T>(value: T | null | undefined, message: string): T {
  if (value == null) {
    throw new Error(message)
  }
  return value
}

const select = xpath.useNamespaces({ cnxml: NS_CNXML, col: NS_COLLECTION, md: NS_METADATA, bk: NS_CONTAINER })
const selectOne = (sel: string, doc: Node): Element => {
  const ret = select(sel, doc) as Node[]
  expectValue(ret.length === 1 || null, `ERROR: Expected one but found ${ret.length} results that match '${sel}'`)
  return ret[0] as Element
}


const BOOK_WEB_ROOT = 'https://openstax.org/details/books/'
const LICENSE_TEXT_MAP: Record<string, string> = {
  'by':
    'Creative Commons Attribution License',
  'by-nd':
    'Creative Commons Attribution-NoDerivs License',
  'by-nd-nc':
    'Creative Commons Attribution-NoDerivs-NonCommercial License',
  'by-sa':
    'Creative Commons Attribution-ShareAlike License',
  'by-nc':
    'Creative Commons Attribution-NonCommercial License',
  'by-nc-sa':
    'Creative Commons Attribution-NonCommercial-ShareAlike License',
}

interface License {
  url: string,
  type: string,
  version: string,
  text: string
}

interface ColMeta {
  title: string,
  license: License
}

interface SlugMeta {
  slugName: string,
  collectionId: string,
  href: string,
  colMeta: ColMeta
}

interface BookMeta {
  slugsMeta: SlugMeta[]
}

function getLicense(license: Element): License {
  let url = expectValue(license.getAttribute('url'), 'No license url')
  let text: string | undefined
  const isLocalized = url.includes('/deed.')
  if (url.endsWith('/')) {
    url = url.slice(0, url.length - 1)
  }
  const [type, version] = (
    isLocalized ? url.slice(0, url.lastIndexOf('/deed.')) : url
  ).split('/').slice(-2)
  text = isLocalized || !(type in LICENSE_TEXT_MAP)
    ? license.textContent?.trim()
    : LICENSE_TEXT_MAP[type]
  if (text === undefined || text.length === 0) {
    throw new Error('Expected license text')
  }
  
  return { url, type, version, text }
}

function getCollectionMeta(colPath: string): ColMeta {
  const metaXpath = '//*[local-name() = "metadata"]'
  const titleXpath = `${metaXpath}/md:title`
  const licenseXpath = `${metaXpath}/md:license`

  const collection = fs.readFileSync(colPath, { encoding: 'utf-8' })
  const doc = new DOMParser().parseFromString(collection)
  const title = expectValue(selectOne(titleXpath, doc).textContent, 'No title')
  const licenseEl = selectOne(licenseXpath, doc)

  return {
    title: title,
    license: getLicense(licenseEl)
  }
}

function getBookMeta(bookPath: string): BookMeta {
  const booksXmlPath = getBooksXmlPath(bookPath)
  const booksXml = fs.readFileSync(booksXmlPath, { encoding: 'utf-8' })
  const doc = new DOMParser().parseFromString(booksXml)
  const slugsMeta: SlugMeta[] = []
  const slugs = select('//*[@slug]', doc) as Element[]
  for (const slug of slugs) {
    const slugName = expectValue(slug.getAttribute('slug'), 'Slug not found')
    const href = expectValue(slug.getAttribute('href'), 'Slug href not found')
    const collectionId = expectValue(
      slug.getAttribute('collection-id'),
      'collection-id not found'
    )
    const colPath = getColPath(booksXmlPath, href)
    const colMeta = getCollectionMeta(colPath)
    slugsMeta.push({ slugName, collectionId, href, colMeta })
  }
  return { slugsMeta }
}

function getBooksXmlPath(bookPath: string) {
  return path.join(bookPath, 'META-INF', 'books.xml')
}

function getColPath(booksXmlPath: string, href: string): string {
  return path.join(path.dirname(booksXmlPath), href)
}

function writeReadme(meta: BookMeta, bookPath: string, templateDir: string) {
  fs.writeFileSync(
    path.join(bookPath, 'README.md'),
    meta.slugsMeta.length === 1
      ? createBookReadme(templateDir, meta.slugsMeta[0])
      : createBundleReadme(templateDir, meta.slugsMeta)
  )
}

function createBookReadme(templateDir: string, slugMeta: SlugMeta) {
  const templatePath = path.join(templateDir, 'book.md')
  const replacements = {
    'book_title': slugMeta.colMeta.title,
    'book_link': `${BOOK_WEB_ROOT}${encodeURIComponent(slugMeta.slugName)}`,
    'license_text': slugMeta.colMeta.license.text,
    'license_type': slugMeta.colMeta.license.type,
    'license_version': slugMeta.colMeta.license.version
  }
  return populateTemplate(templatePath, replacements)
}

function licenseEqual(a: License, b: License) {
  return a.type === b.type &&
    a.text === b.text &&
    a.url === b.url &&
    a.version === b.version
}

function createBundleReadme(templateDir: string, slugsMeta: SlugMeta[]) {
  const templatePath = path.join(templateDir, 'bundle.md')
  const license = slugsMeta[0].colMeta.license
  if (!slugsMeta.every(sm => licenseEqual(sm.colMeta.license, license))) {
    throw new Error('Licenses differ between collections')
  }
  const replacements = {
    'book_titles':
      slugsMeta.map((s, i) =>
        i === slugsMeta.length - 1 ? `and ${s.colMeta.title}` : s.colMeta.title
      ).join(slugsMeta.length > 2 ? ', ' : ' '),
    'book_links':
      slugsMeta.map(s =>
        `- _${s.colMeta.title}_ [online](${BOOK_WEB_ROOT}${encodeURIComponent(s.slugName)})`
      ).join('\n'),
    'license_text': license.text,
    'license_type': license.type,
    'license_version': license.version
  }
  return populateTemplate(templatePath, replacements)
}

function populateTemplate(templatePath: string, replacements: Record<string, string>) {
  let template = fs.readFileSync(templatePath, { encoding: 'utf-8' })
  // '{{ x }}' -> replacements['x']
  return template.replace(new RegExp('\{{2}.+?\}{2}', 'g'), m => {
    const prop = m.slice(2, -2)
    const value = replacements[prop.trim()]
    if (value === undefined) {
      throw new Error(`${prop} is undefined`)
    }
    return value
  })
}

function copyRepoSettings(bookPath: string, settingsDir: string) {
  function recCopyDir(src: string, dst: string) {
    if (!fs.existsSync(dst)) {
      fs.mkdirSync(dst)
    }
    for (const dirent of fs.readdirSync(src, { withFileTypes: true })) {
      if (dirent.isDirectory()) {
        recCopyDir(
          path.join(src, dirent.name),
          path.join(dst, dirent.name)
        )
      } else if (dirent.isFile()) {
        fs.copyFileSync(
          path.join(src, dirent.name),
          path.join(dst, dirent.name)
        )
      }
    }
  }
  recCopyDir(settingsDir, bookPath)
}

function prepareBookRepo(bookPath: string, staticResourceDir: string) {
  const meta = getBookMeta(bookPath)
  writeReadme(meta, bookPath, staticResourceDir)
  copyRepoSettings(bookPath, path.join(staticResourceDir, 'repo-settings'))
  
  // This is a temporary addition so that the python script can handle the
  // license related work that is out of the scope of this script
  console.log(JSON.stringify(meta))
}

prepareBookRepo(process.argv[2], path.join(__dirname, 'static'))
